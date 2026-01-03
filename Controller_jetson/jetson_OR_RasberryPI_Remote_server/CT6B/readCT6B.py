import serial
import time
from typing import List, Optional

# --- Configuration ---
PORT = 'COM9'  # <-- CONFIRMED: Update this if needed
BAUD = 115200  # <-- CONFIRMED: This baud rate is correct
TIMEOUT = 1    
# --- End Configuration ---

def parse_packet(packet: bytearray) -> Optional[List[int]]:
    """
    Parse a single 18-byte packet from FS-CT6B trainer port.
    Uses the verified '55 FC' header and standard checksum.
    """
    # 1. Check Header (0x55 0xFC) and Length (18 bytes)
    # The header is changed from 0xA5 to 0x55 based on your raw data.
    if len(packet) < 18 or packet[0] != 0x55 or packet[1] != 0xFC: 
        return None
    
    # 2. Decode 7 Channels (10-bit values, Big-Endian)
    channels = []
    for j in range(7):
        high = packet[2 + 2 * j]
        low = packet[3 + 2 * j]
        ch_val = (high << 8) | low
        channels.append(ch_val)
    
    # 3. Checksum Calculation (Bytes 2-15) - Simple Sum
    ch_sum = sum(packet[2:16])
    
    # Expected Checksum components
    expected_high = ch_sum // 256
    expected_low = ch_sum % 256
    
    # Actual Checksum components from the packet
    actual_high = packet[16]
    actual_low = packet[17]
    
    # 4. Validation
    valid = (expected_high == actual_high) and (expected_low == actual_low)
    
    return channels if valid else None

def main():
    try:
        ser = serial.Serial(
            port=PORT,
            baudrate=BAUD,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=TIMEOUT
        )
    except serial.SerialException as e:
        print(f"Error opening serial port {PORT}: {e}")
        print("Please check if the port is correct and not in use by another program.")
        return
    
    print(f"Connected to {PORT} at {BAUD} baud. Reading and decoding FS-CT6B data...")
    print("Move sticks/switches to see channel changes. Ctrl+C to stop.")
    print("Format: [Roll, Pitch, Throttle, Yaw, Ch5, Ch6, Ch7] (0-2047 range)")
    print("-" * 70)
    
    buffer = bytearray()
    packet_count = 0
    try:
        while True:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                buffer.extend(data)
                
            # Process complete packets
            while True:
                # Find the CORRECTED packet header (b'\x55\xFC')
                idx = buffer.find(b'\x55\xFC')
                
                # Break if header is not found or a full packet is not available
                if idx == -1 or idx + 18 > len(buffer):
                    if idx != -1:
                        # Trim junk data before the start of the next header
                        del buffer[:idx]
                    break
                
                # Extract the 18-byte packet
                pkt = buffer[idx:idx + 18]
                decoded = parse_packet(pkt)
                
                if decoded:
                    packet_count += 1
                    print(f"Packet #{packet_count}: {decoded}")
                # else: Invalid packets are discarded
                
                # Remove the parsed 18-byte chunk from the buffer
                del buffer[:idx + 18]
            
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print(f"\nStopped. Processed {packet_count} valid packets.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()