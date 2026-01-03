import serial
from typing import List, Optional
import asyncio
class CT6BReceiver:
    """
    Handles serial port communication, packet buffering, and decoding 
    of FS-CT6B trainer port data.
    """
    def __init__(self, port: str, baud: int):
        self.port = port
        self.baud = baud
        self.ser: Optional[serial.Serial] = None
        self.buffer = bytearray()
        self.queue = asyncio.Queue(maxsize=10)

    def connect(self):
        """Opens the serial port."""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1 # Small timeout for non-blocking read
            )
            print(f"✅ Successfully opened serial port {self.port} at {self.baud} baud.")
            return True
        except serial.SerialException as e:
            print(f"❌ Error opening serial port {self.port}: {e}")
            print("Please check if the port is correct and not in use.")
            return False

    def close(self):
        """Closes the serial port."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print(f"[INFO] Serial port {self.port} closed.")

    def parse_packet(self, packet: bytearray) -> Optional[List[int]]:
        """
        Parse a single 18-byte packet from FS-CT6B trainer port.
        Returns a list of 7 channel values (0-2047) if valid, otherwise None.
        """
        # 1. Check Header (0x55 0xFC) and Length (18 bytes)
        if len(packet) < 18 or packet[0] != 0x55 or packet[1] != 0xFC:
            return None
        
        # 2. Decode 7 Channels (10-bit values, Big-Endian)
        channels = []
        for j in range(7):
            # Channels are Big-Endian: high byte (ChX+0), low byte (ChX+1)
            high = packet[2 + 2 * j]
            low = packet[3 + 2 * j]
            ch_val = (high << 8) | low
            channels.append(ch_val)
        
        # 3. Checksum Calculation (Bytes 2-15) - Simple Sum
        ch_sum = sum(packet[2:16])
        
        expected_high = ch_sum // 256
        expected_low = ch_sum % 256
        
        actual_high = packet[16]
        actual_low = packet[17]
        
        # 4. Validation
        valid = (expected_high == actual_high) and (expected_low == actual_low)
        
        return channels if valid else None

    async def run_reader(self):
        """Asynchronously reads serial data and processes packets."""
        if not self.ser or not self.ser.is_open:
            print("❌ Serial port is not open.")
            return

        print("Serial reader active. Waiting for CT6B data...")
        
        while self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)
                    self.buffer.extend(data)
                
                # Process complete packets in the buffer
                while True:
                    idx = self.buffer.find(b'\x55\xFC')
                    
                    if idx == -1 or idx + 18 > len(self.buffer):
                        if idx != -1: 
                            del self.buffer[:idx]
                        break
                    
                    pkt = self.buffer[idx:idx + 18]
                    decoded_channels = self.parse_packet(pkt)
                    
                    if decoded_channels:
                        # Put the full 7-channel list into the queue
                        await self.queue.put(decoded_channels)
                        
                    del self.buffer[:idx + 18]
                
                await asyncio.sleep(0.001)
            except serial.SerialException as e:
                print(f"\n[ERROR] Serial read error: {e}")
                break
            except Exception as e:
                print(f"\n[ERROR] Unexpected error in serial reader: {e}")
                break