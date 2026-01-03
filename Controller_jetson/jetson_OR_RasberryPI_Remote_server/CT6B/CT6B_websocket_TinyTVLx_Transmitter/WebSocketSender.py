# --- WebSocketSender.py ---

import asyncio
import websockets
import struct
from typing import List
# Import the TinyTLVTx class AND the necessary constants
from tinytlvx import TinyTLVTx, TTP_FRAME_TYPE_RC 

# Removed: TTP_STX, TTP_MAX_FRAME, TTP_FRAME_TYPE_RC are now imported from tinytlvx

class WebSocketSender:
    """
    Handles the WebSocket connection and sends channel data encoded 
    using the TinyTLVTx format.
    """
    def __init__(self, ws_uri: str, receiver_queue: asyncio.Queue):
        self.ws_uri = ws_uri
        self.receiver_queue = receiver_queue
        # Naming consistency: Use the official imported class name
        self.tlv_tx = TinyTLVTx()
        
    def pack_channels_to_tlv(self, channels: List[int]) -> bytes:
        """
        Converts the 7 channel values (0-2047) into a TTP frame 
        with each channel as a 2-byte (u16) TLV block.
        """
        # Use the imported constant for the frame type
        self.tlv_tx.begin(TTP_FRAME_TYPE_RC)
        
        for ch_id, ch_val in enumerate(channels):
            # Channel value (u16, Little-Endian '<H')
            # Max value is 2047, which fits easily in u16.
            ch_data = struct.pack('<H', ch_val)
            # ID is channel index, Length is 2 bytes
            self.tlv_tx.addTLV(ch_id, 2, ch_data) 
            
        return self.tlv_tx.end()

    async def run_sender(self):
        """Connects to WebSocket and sends TTP frames from the queue."""
        while True:
            try:
                # Replaced the placeholder WS_URI with the actual configuration
                async with websockets.connect(self.ws_uri) as websocket:
                    print(f"🌐 WebSocket connected to {self.ws_uri}")
                    print("Starting TinyTLV data transmission...")
                    
                    while True: 
                        channels = await self.receiver_queue.get()
                        tlv_frame = self.pack_channels_to_tlv(channels)
                        await websocket.send(tlv_frame)
                        self.receiver_queue.task_done()
                
            except websockets.exceptions.ConnectionClosed as e:
                print(f"\n[WARNING] WebSocket connection closed: {e.code}/{e.reason}. Reconnecting in 5 seconds...")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"\n[ERROR] WebSocket error: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(5)