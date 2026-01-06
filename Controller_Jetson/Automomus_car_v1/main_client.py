import asyncio
import sys
import time

from serialSender import SerialSender
from RCDataDecoder import RCDataDecoder
from rc_mixer import RCMixer
from health_monitor import HealthMonitor
from control_process import PID

# Configuration
WS_URI = "ws://yadiec2.freedynamicdns.net:8080/ws"
HEALTH_URL = "http://yadiec2.freedynamicdns.net:8080/health"
SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200
MODE = "MANUAL"

AUTO_MODE_TRIGGER = 1700    # If Aux1 > 1700, switch to AUTO


async def main(shared_angle, shared_seq):
    motor_serial = SerialSender(port=SERIAL_PORT, baudrate=BAUD_RATE)
    if not motor_serial.open_serial():
        print("❌ Failed to open serial port. Exiting.")
        sys.exit(1)

    health = HealthMonitor(endpoint_url=HEALTH_URL, interval=2.0)
    client = RCDataDecoder(ws_uri=WS_URI)
    asyncio.ensure_future(client.run_receiver())

    # Initialize the PID Controller once
    # pid = SteeringPID(kp=1.2, ki=0.01, kd=0.05)
    steering_pid = PID(kp=5, ki=0.1, kd=0.1, setpoint=0)
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
            
            # --- 2. HANDLE PID CONFIG UPDATES ---
            # Check if this is a Config frame
            if data.get("_type") == "CONFIG":
                # IDs are mapped in RCDataDecoder.py RC_CHANNELS
                if "Kp" in data: steering_pid.kp = data["Kp"]
                if "Ki" in data: steering_pid.ki = data["Ki"]
                if "Kd" in data: steering_pid.kd = data["Kd"]
                # print(f"⚙️ PID Parameters Updated: P={steering_pid.kp}, I={steering_pid.ki}, D={steering_pid.kd}")
                # We don't want to run motor logic on a pure config packet, 
                # so we wait for the next RC packet.
                continue 

            # --- 3. MODE SELECTION & MOTOR CONTROL ---
            # This part only runs if it's NOT a config packet or after timing is updated
            aux1 = data.get("Aux1", 1000)
   
            # --- MODE SELECTION & EXECUTION ---
            # We check the local RC data to see if the user wants Manual or Auto
            # Usually, we use a switch like Aux1
            
            aux1 = data.get("Aux1", 1000) if data else 1000
            # print(aux1)
            if aux1 < AUTO_MODE_TRIGGER:
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
            
            # --- SAFETY & MIXING ---
            # If we haven't seen web data in 1 second, safety stop
            if (time.time() - last_valid_packet_local_time) > 1.0:
                motor_serial.stop()
            else:
                # Mix throttle/roll into motor commands
                direction, pwm1, pwm2 = RCMixer.compute_motor_commands(throttle, roll, aux1)
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