# --- main_control.py ---
import asyncio
import sys
import time

# Import your existing library
from serialSender import SerialSender 
# Import the new modules
from RCDataDecoder import RCDataDecoder
from rc_mixer import RCMixer

# Configuration
WS_URI = "ws://yadiec2.freedynamicdns.net:8080/ws" # Update to your ngrok address if needed
SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200

async def main():
    # 1. Initialize Serial Sender
    motor_serial = SerialSender(port=SERIAL_PORT, baudrate=BAUD_RATE)
    if not motor_serial.open_serial():
        print("❌ Failed to open serial port. Exiting.")
        sys.exit(1)

    # 2. Initialize WebSocket Receiver
    client = RCDataDecoder(ws_uri=WS_URI)

    # 3. Start the Receiver in the background
    # asyncio.ensure_future is compatible with Python 3.6+
    asyncio.ensure_future(client.run_receiver())
    ast_valid_packet_time = time.time()

    # Tracks the last time we processed a valid, "fresh" packet
    last_valid_packet_time = time.time()
    

    print("🚀 Motor Control System Started with Latency Protection.")
    print("Waiting for RC data...")

    try:
        # 4. Main Control Loop (Runs at approx 20Hz)
        while True:
            # Control loop speed (50ms = 20Hz)
            await asyncio.sleep(0.05) 

            # Fetch latest data from the decoder class
            # current_time_ms = int(time.time() * 1000)
            current_time_ms = int(time.time() * 1000) & 0xFFFFFFFF 

            data = client.get_latest_data()
            #print(data)
            #print((time.time() - last_valid_packet_time)* 1000)
            if not data:
                # No data received yet, skip this cycle
                if time.time() - last_valid_packet_time > 1.0:
                    motor_serial.stop()
                    

                continue

	    # 1. Extract embedded timestamp from sender
            packet_timestamp = data.get("timestamp", 0)
            latency = current_time_ms - packet_timestamp

            # 2. Check for stale data (Discard if latency > 1000ms)
            if latency > 1000:
                # Packet is too old; don't process it.
                # Check if we need to emergency stop due to lack of fresh data
                if (time.time() - last_valid_packet_time) > 1.0:
                    # print(f"⚠️ High Latency ({latency}ms) or No Data. Sending STOP.")
                    motor_serial.stop()
                continue

            # 3. If we reached here, the packet is fresh!
            last_valid_packet_time = time.time() # Update watchdog
            # Safely get values (Default to 1500/Center if key missing)
            throttle            = data.get("Pitch", 1500)
            roll                = data.get("Roll", 1500)
            rc_reft_right_mixer = data.get("Aux1", 1500)
            # Use the Mixer class to calculate motor values
            direction, pwm1, pwm2 = RCMixer.compute_motor_commands(throttle, roll,rc_reft_right_mixer)

            # Debug output (optional, uncomment to see live values)
            # print(f"Thr: {throttle} Rol: {roll} -> Dir: {direction} L: {pwm1} R: {pwm2}")

            # Send to motors using your library
            motor_serial.send_motor_command(direction, pwm1, pwm2)

    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
        motor_serial.stop()
    finally:
        motor_serial.close_serial()

if __name__ == "__main__":
    # Python 3.6 compatible execution
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
