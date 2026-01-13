# main_client.py  (Python 3.6 SAFE)

import asyncio
import sys
import time

from serialSender import SerialSender
from RCDataDecoder import RCDataDecoder
from rc_mixer import RCMixer
from health_monitor import HealthMonitor
from PID_Controll import PID
import TelemetryOutput
import config


async def main(shared_angle, shared_seq, loop):
    # ------------------ SERIAL ------------------
    motor_serial = SerialSender(
        port=config.SERIAL_PORT,
        baudrate=config.BAUD_RATE
    )

    if not motor_serial.open_serial():
        print("❌ Failed to open serial port. Exiting.")
        sys.exit(1)

    # ------------------ HEALTH ------------------
    health = HealthMonitor(
        endpoint_url=config.HEALTH_URL,
        interval=config.HEALTH_CHECK_INTERVAL,
        loop=loop      # IMPORTANT
    )

    # ------------------ WEBSOCKET ------------------
    client = RCDataDecoder(
        ws_uri=config.WS_URI,
        loop=loop      # IMPORTANT
    )

    # Start receiver task (Python 3.6 SAFE)
    ws_task = loop.create_task(client.run())

    # ------------------ PID ------------------
    steering_pid = PID(
        kp=config.PID_KP,
        ki=config.PID_KI,
        kd=config.PID_KD,
        setpoint=config.PID_SETPOINT,
        output_limits=config.PID_OUTPUT_LIMITS
    )

    last_processed_timestamp = -1
    last_valid_packet_local_time = time.time()
    clock_offset = None
    latency = 0
    ema_error = 0.0
    ema_error_initialized = False

    ema_correction = 0.0
    ema_correction_initialized = False
 
    print("🚀 Motor Control System Started. Waiting for data...")

    try:
        while True:
            await asyncio.sleep(0.02)

            data = client.get_latest_data()
            # print(data)
            now = time.time()

            # ------------------ HEALTH ------------------
            health.update(
                int(latency),
                int(last_valid_packet_local_time * 1000)
            )

            if not data:
                continue
             # ------------------ Read voltage and current from motor ------------------
            try:
                tele_data = motor_serial.read_telemetry()
                if tele_data is None:
                    continue   # No more full packets in the buffer
                
                v, i, p = tele_data
                # status = "Charging" if i < 0 else "Discharging"
                # # Logic for health monitor or logging
                # print(f"[{status}] {v:.2f}V | {i:.1f}mA")
            except Exception as e:
                print(f"Telemetry Read Error: {e}")
            # ------------------ LATENCY ------------------
            packet_ts = data.get("timestamp")
            if packet_ts is not None:
                if packet_ts != last_processed_timestamp:
                    current_local_ms = int(now * 1000) & 0xFFFFFFFF
                    raw_diff = (current_local_ms - packet_ts) & 0xFFFFFFFF
                    
                    if clock_offset is None:
                        clock_offset = raw_diff - 30
                    
                    latency = (raw_diff - clock_offset) & 0xFFFFFFFF
                    last_valid_packet_local_time = now
                    last_processed_timestamp = packet_ts
                   

            # ------------------ CONFIG UPDATE ------------------
            if data.get("_type") == "CONFIG":
                steering_pid.set_tunings(
                    kp=data.get("Kp", steering_pid.kp),
                    ki=data.get("Ki", steering_pid.ki),
                    kd=data.get("Kd", steering_pid.kd)
                )
                continue

            # ------------------ MODE ------------------
            aux1 = data.get("Aux1", 1000)

            if aux1 < config.AUTO_MODE_TRIGGER:
                # MANUAL
                throttle = data.get("Pitch", 1500)
                roll = data.get("Roll", 1500)
                # print(data)
                json_string = f'{{"motorTelemetry": {{"V": {v:.2f}, "I": {i:.2f}, "P": {p:.2f}}}}}'

                TelemetryOutput.send(json_string, 0.1)   
            else:
                # AUTO
                raw_error = float(shared_angle.value)

                # -------- EMA on ERROR (input smoothing) --------
                if not ema_error_initialized:
                    ema_error = raw_error
                    ema_error_initialized = True
                else:
                    ema_error = (
                        config.EMA_ALPHA_ERROR * raw_error +
                        (1.0 - config.EMA_ALPHA_ERROR) * ema_error
                    )

                filtered_error = ema_error

                # -------- PID --------
                raw_correction = steering_pid.compute(filtered_error)

                # -------- EMA on CORRECTION (output smoothing) --------
                if not ema_correction_initialized:
                    ema_correction = raw_correction
                    ema_correction_initialized = True
                else:
                    ema_correction = (
                        config.EMA_ALPHA_CORRECTION * raw_correction +
                        (1.0 - config.EMA_ALPHA_CORRECTION) * ema_correction
                    )

                correction = ema_correction

                # -------- Actuation --------
                throttle = data.get("Pitch", 1500)
                roll = int(1500 + correction)


                # build a output telemetry JSON
                json_string = f'{{"error":{filtered_error},"correction":{ema_correction},"throttle":{throttle} ,"V": {v} ,"I": {i},"P":{p} }}'

                TelemetryOutput.send(json_string, 0.2)

            # ------------------ SAFETY ------------------
            if (now - last_valid_packet_local_time) > 1.0:
                motor_serial.stop()
            else:
                direction, pwm1, pwm2 = RCMixer.compute_motor_commands(
                    roll, throttle, config.MOTOR_OFFSET_CORRECT
                )
                motor_serial.send_motor_command(direction, pwm1, pwm2)

    except KeyboardInterrupt:
        print("🛑 Shutting down...")

    finally:
        print("Cleaning up tasks...")

        ws_task.cancel()
        try:
            await ws_task
        except asyncio.CancelledError:
            pass

        motor_serial.stop()
        motor_serial.close_serial()

        await health.close()


def run_main(shared_angle, shared_seq):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.set_debug(True)

    try:
        loop.run_until_complete(main(shared_angle, shared_seq, loop))
    finally:
        loop.close()


if __name__ == "__main__":
    run_main(None, None)  # replace with your shared memory objects
