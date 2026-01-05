import asyncio
import sys
import time

from serialSender import SerialSender
from RCDataDecoder import RCDataDecoder
from rc_mixer import RCMixer
from health_monitor import HealthMonitor

# Configuration
WS_URI = "ws://yadiec2.freedynamicdns.net:8080/ws"
HEALTH_URL = "http://yadiec2.freedynamicdns.net:8080/health"
SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200

async def main():
    motor_serial = SerialSender(port=SERIAL_PORT, baudrate=BAUD_RATE)
    if not motor_serial.open_serial():
        print("❌ Failed to open serial port. Exiting.")
        sys.exit(1)

    health = HealthMonitor(endpoint_url=HEALTH_URL, interval=2.0)
    client = RCDataDecoder(ws_uri=WS_URI)
    asyncio.ensure_future(client.run_receiver())

    # --- Timing Variables ---
    last_processed_timestamp = -1
    last_valid_packet_local_time = time.time()
    latency = 0
    clock_offset = None  # To handle unsynced clocks

    print("🚀 Motor Control System Started.")

    try:
        while True:
            await asyncio.sleep(0.05) # 20Hz
            
            current_local_ms = int(time.time() * 1000) & 0xFFFFFFFF
            data = client.get_latest_data()
            packet_timestamp = data.get("timestamp", 0) if data else None
            
            # 1. Check if we have a NEW packet
            if data and packet_timestamp != last_processed_timestamp:
                
                # Calculate raw difference
                raw_diff = (current_local_ms - packet_timestamp) & 0xFFFFFFFF
                
                # Initialize clock offset on the first packet
                # This treats the first packet as having ~30ms latency base
                if clock_offset is None:
                    clock_offset = raw_diff - 30
                    print(f"✅ Sync established. Clock Offset: {clock_offset}")

                # Calculate relative latency
                latency = (raw_diff - clock_offset) & 0xFFFFFFFF
                
                # Sanity check: if latency is huge, it's a wrap-around or glitch
                if latency > 0x7FFFFFFF: latency = 0 

                last_valid_packet_local_time = time.time()
                last_processed_timestamp = packet_timestamp

                # 2. Logic: Only process if latency is under 1 second
                if latency < 1000:
                    throttle = data.get("Pitch", 1500)
                    roll     = data.get("Roll", 1500)
                    aux1     = data.get("Aux1", 1500)
                    direction, pwm1, pwm2 = RCMixer.compute_motor_commands(throttle, roll, aux1)
                    motor_serial.send_motor_command(direction, pwm1, pwm2)
                else:
                    motor_serial.stop()
            
            else:
                # 3. No new data: Check how long since the last packet arrived
                ms_since_last = (time.time() - last_valid_packet_local_time) * 1000
                
                if ms_since_last > 1000:
                    latency = 0 # As per your request: no latency if no continuous data
                    motor_serial.stop()

            # 4. Update Health Monitor
            # last_valid_packet_local_time is passed as a 32-bit MS timestamp
            # ms_since_last = int((time.time() - last_valid_packet_local_time) * 1000)
            health.update(int(latency), int(last_valid_packet_local_time * 1000))

    except KeyboardInterrupt:
        motor_serial.stop()
    finally:
        await health.close()
        motor_serial.close_serial()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()