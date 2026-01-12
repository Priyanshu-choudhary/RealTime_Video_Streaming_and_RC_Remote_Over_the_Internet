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

# Configuration is now imported from config.py


async def main(shared_angle, shared_seq):
    motor_serial = SerialSender(port=config.SERIAL_PORT, baudrate=config.BAUD_RATE)
    if not motor_serial.open_serial():
        print("❌ Failed to open serial port. Exiting.")
        sys.exit(1)

    health = HealthMonitor(endpoint_url=config.HEALTH_URL, interval=config.HEALTH_CHECK_INTERVAL)
    client = RCDataDecoder(ws_uri=config.WS_URI)
    asyncio.ensure_future(client.run_receiver())

    # Initialize the PID Controller once
    # pid = SteeringPID(kp=1.2, ki=0.01, kd=0.05)
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

    print("🚀 Motor Control System Started. Waiting for data...")

    try:
        # --- main_client.py ---

        while True:
            await asyncio.sleep(0.02)
            
            data = client.get_latest_data()
            if not data:
                continue

            # --- 1. HANDLE PACKET TIMING & LATENCY ---
            # We ONLY do this if 'timestamp' is present (which only happens in RC frames)
            packet_ts = data.get("timestamp")
            
            if packet_ts is not None:
                if packet_ts != last_processed_timestamp:
                    current_local_ms = int(time.time() * 1000) & 0xFFFFFFFF
                    raw_diff = (current_local_ms - packet_ts) & 0xFFFFFFFF
                    
                    if clock_offset is None: 
                        clock_offset = raw_diff - 30
                    
                    latency = (raw_diff - clock_offset) & 0xFFFFFFFF
                    last_valid_packet_local_time = time.time()
                    last_processed_timestamp = packet_ts
                    
                    # Only update health monitor if we have valid latency data
                    health.update(int(latency), int(last_valid_packet_local_time * 1000))
            
            
            
            #Read the decoded confid for PID contants
            if data.get("_type") == "CONFIG":
                # IDs are mapped in RCDataDecoder.py RC_CHANNELS
                steering_pid.set_tunings(kp=data["Kp"], ki=data["Ki"], kd=data["Kd"])
                 
            # --- 3. MODE SELECTION & MOTOR CONTROL ---
            # This part only runs if it's NOT a config packet or after timing is updated
            aux1 = data.get("Aux1", 1000)
    
            # --- MODE SELECTION & EXECUTION ---
            # We check the local RC data to see if the user wants Manual or Auto
            
            aux1 = data.get("Aux1", 1000) if data else 1000
            # print(aux1)
            if aux1 < config.AUTO_MODE_TRIGGER:
                # --- MANUAL MODE ---
                throttle = data.get("Pitch", 1500) if data else 1500
                roll = data.get("Roll", 1500) if data else 1500
            else:
                # --- AUTO (PID) MODE ---
                # Read from shared memory updated by Vision Process
                current_error = shared_angle.value

                   

                # Compute PID correction (Steering)
                correction = steering_pid.compute(current_error)
                # print(current_error)
                # IMPROVEMENT: Use the remote throttle (Pitch) from the websocket
                # If data is None, we default to 1500 (neutral/stop)
                throttle = data.get("Pitch", 1500) if data else 1500

                # Apply PID to roll (steering)
                roll = 1500 + correction
                TelemetryOutput.send(f"{current_error} , {correction} , {throttle} , {roll}", 0.1)
            
            # --- SAFETY & MIXING ---
            # If we haven't seen web data in 1 second, safety stop
            if (time.time() - last_valid_packet_local_time) > 1.0:
                motor_serial.stop()
            else:
                # Mix throttle/roll into motor commands
                direction, pwm1, pwm2 = RCMixer.compute_motor_commands(roll, throttle, aux1)
                motor_serial.send_motor_command(direction, pwm1, pwm2)

            health.update(int(latency), int(last_valid_packet_local_time * 1000))

    except KeyboardInterrupt:
        motor_serial.stop()
    finally:
        await health.close()
        motor_serial.close_serial()

def run_main(shared_angle, shared_seq):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main(shared_angle, shared_seq))
    finally:
        loop.close()


if __name__ == "__main__":
    run_main()