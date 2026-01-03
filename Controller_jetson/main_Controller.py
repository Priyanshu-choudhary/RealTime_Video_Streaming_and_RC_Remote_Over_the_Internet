#!/usr/bin/env python3
import asyncio
import sys
from serialSender import SerialSender
from webClass import WebSocketDecoder
import time

MAX_PWM_OUTPUT = 100
RC_MIN = 1000
RC_MAX = 2000
RC_CENTER = 1500
RC_HALF_RANGE = 500.0  # 1500 +/- 500 -> [1000,2000]
RC_DEADBAND = 30       # microseconds around center considered zero (tweakable)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def rc_to_signed_255(rc):
    """Convert RC (1000..2000) to signed -255..255 where 1500 -> 0."""
    rc = clamp(int(rc), RC_MIN, RC_MAX)
    return int(round((rc - RC_CENTER) / RC_HALF_RANGE * 255))


def compute_motor_commands(throttle_rc, roll_rc, rc_deadband=RC_DEADBAND):
    """
    Return (direction, pwm_motor1, pwm_motor2)
    direction: 1 forward, 2 reverse, 0 stop, 3 pivot right, 4 pivot left
    pwm_motorX: 0..255 (magnitude)
    """
    # clamp inputs
    throttle_rc = clamp(int(throttle_rc), RC_MIN, RC_MAX)
    roll_rc = clamp(int(roll_rc), RC_MIN, RC_MAX)

    thr_delta = throttle_rc - RC_CENTER
    roll_delta = roll_rc - RC_CENTER

    # Apply deadband in RC units
    if abs(thr_delta) <= rc_deadband:
        th_signed = 0
    else:
        th_signed = rc_to_signed_255(throttle_rc)

    if abs(roll_delta) <= rc_deadband:
        roll_signed = 0
    else:
        roll_signed = rc_to_signed_255(roll_rc)

    # Stop if both near center
    if th_signed == 0 and roll_signed == 0:
        return 0, 0, 0

    # If throttle is zero-ish and roll present -> pivot in place
    if th_signed == 0 and roll_signed != 0:
        pwm = clamp(abs(roll_signed), 0, MAX_PWM_OUTPUT)
        if roll_signed > 0:
            # roll positive => pivot right (left forward, right reverse)
            return 3, pwm, pwm
        else:
            # roll negative => pivot left
            return 4, pwm, pwm

    # Normal mixing when throttle significant
    left_signal = th_signed + roll_signed
    right_signal = th_signed - roll_signed

    # clamp signals to signed -255..255
    left_signal = clamp(left_signal, -255, 255)
    right_signal = clamp(right_signal, -255, 255)

    # If they are opposite signs and roll dominates throttle -> pivot
    if left_signal * right_signal < 0 and abs(roll_signed) > abs(th_signed):
        pwm = clamp(max(abs(left_signal), abs(right_signal)), 0, MAX_PWM_OUTPUT)
        if roll_signed > 0:
            return 3, pwm, pwm
        else:
            return 4, pwm, pwm

    # Otherwise direction follows throttle sign (average = throttle)
    if th_signed > 0:
        # Forward: take positive parts, zero negatives
        pwm_l = clamp(max(0, left_signal), 0, MAX_PWM_OUTPUT)
        pwm_r = clamp(max(0, right_signal), 0, MAX_PWM_OUTPUT)
        return 1, int(pwm_l), int(pwm_r)
    else:
        # Reverse: take absolute of negative parts
        pwm_l = clamp(max(0, -left_signal), 0, MAX_PWM_OUTPUT)
        pwm_r = clamp(max(0, -right_signal), 0, MAX_PWM_OUTPUT)
        return 2, int(pwm_l), int(pwm_r)


async def main():
    # Initialize serial sender
    serial = SerialSender(port="/dev/ttyUSB0", baudrate=115200)
    if not serial.open_serial():
        print("Failed to open serial port")
        sys.exit(1)

    try:
        # Initialize WebSocket receiver
        client = WebSocketDecoder("wss://unmelodramatically-nonoxidating-mana.ngrok-free.dev/ws")
        await client.connect()
        asyncio.ensure_future(client.listen())

        # Main loop: update ~20 Hz
        while True:
            await asyncio.sleep(0.05)
            last_data = client.get_last_data()
            if not last_data:
                continue

            throttle = int(last_data.Throttle)
            roll = int(last_data.Roll)
            aux1 = getattr(last_data, "Aux1", None)
            aux2 = getattr(last_data, "Aux2", None)

            direction, pwm1, pwm2 = compute_motor_commands(throttle, roll)

            # Debug print
#            print(
 #               f"RC T:{throttle} R:{roll} -> dir:{direction} pwm1:{pwm1} pwm2:{pwm2} (aux1:{aux1} aux2:{aux2})"
  #          )

            # Send to motor controller (direction, pwm motor1, pwm motor2)
            serial.send_motor_command(direction, pwm1, pwm2)
            # time.sleep(300)

    except KeyboardInterrupt:
        print("\nStopped by user.")
        serial.stop()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        serial.close_serial()
        sys.exit(0)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()