import asyncio
import websockets
import struct
import time
from typing import Dict, Any
from tinytlvx import TinyTLVRx, TTP_FRAME_TYPE_RC, TTP_FRAME_TYPE_CONFIG
import TelemetryOutput

# Define channel names and PID parameters
RC_CHANNELS = {
    # Driving Channels
    0: "Roll",     
    1: "Pitch",    
    2: "Throttle", 
    3: "Yaw",      
    4: "Aux1",     
    5: "Aux2",     
    
    # PID Tuning Channels (Sent via Smart addTVL as floats)
    10: "Kp",
    11: "Ki",
    12: "Kd",
    
    # Timing
    100: "timestamp"
}

CONFIG = {
    # PID Tuning Channels (Sent via Smart addTVL as floats)
    1: "Kp",
    2: "Ki",
    3: "Kd",
}

class RCDataDecoder:
    """
    Handles WebSocket connection and stores the latest decoded RC and Config data.
    """
    def __init__(self, ws_uri: str):
        self.ws_uri = ws_uri
        self.rx = TinyTLVRx() 
        self.latest_data = {} 

    def get_latest_data(self) -> Dict[str, Any]:
        """Returns the most recent decoded data."""
        return self.latest_data

    def decode_rc_data(self) -> Dict[str, Any]:
        """Internal helper to parse TLVs based on the current frame type."""
        frame_type = self.rx.getType()
        decoded_values = {}

        # --- HANDLE CONFIG FRAMES (IDs 10, 11, 12 as Floats) ---
        if frame_type == TTP_FRAME_TYPE_CONFIG:
            self.rx.beginTLV()
            while True:
                tlv = self.rx.nextTLV()
                if tlv is None: break
                
                ch_id, length, data = tlv
                
                if length == 4:
                    # Interpret 4-byte values in CONFIG as Float32
                    value = struct.unpack('<f', data)[0]
                    ch_name = CONFIG.get(ch_id, f"PID_Param_{ch_id}")
                    decoded_values[ch_name] = value
                elif length == 2:
                    # Legacy or small integer config
                    value = struct.unpack('<H', data)[0]
                    ch_name = CONFIG.get(ch_id, f"Config_{ch_id}")
                    decoded_values[ch_name] = value

            decoded_values["_type"] = "CONFIG"
            
            return decoded_values

        # --- HANDLE RC DATA (Driving & Timing) ---
        elif frame_type == TTP_FRAME_TYPE_RC:
            self.rx.beginTLV()
            while True:
                tlv = self.rx.nextTLV()
                if tlv is None: break
                
                ch_id, length, data = tlv
                
                if ch_id == 100 and length == 4:
                    # Timestamp is a Uint32
                    decoded_values["timestamp"] = struct.unpack('<I', data)[0]
                elif length == 2:
                    # RC Channels (Roll, Pitch, etc.) are Uint16
                    value = struct.unpack('<H', data)[0]
                    ch_name = RC_CHANNELS.get(ch_id, f"Channel_{ch_id}")
                    decoded_values[ch_name] = value
            
            decoded_values["_type"] = "RC"
            return decoded_values

        return {}

    async def run_receiver(self):
        """Websocket client loop."""
        while True:
            try:
                async with websockets.connect(self.ws_uri) as websocket:
                    print(f"🔗 Connected to {self.ws_uri}")
                    self.rx.reset()
                    
                    # Create Sender Task
                    sender_task = asyncio.create_task(self.sender_loop(websocket))
                    
                    try:
                        while True:
                            message = await websocket.recv()
                        
                        # Capture exact arrival time
                        arrival_ts = int(time.time() * 1000) & 0xFFFFFFFF 
                        
                        if isinstance(message, str): 
                            continue

                        for byte in message:
                            if self.rx.feed(byte):
                                new_data = self.decode_rc_data()
                                if new_data:
                                    # Attach metadata
                                    new_data["arrival_ts"] = arrival_ts
                                    self.latest_data = new_data
                                    
            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError):
                if 'sender_task' in locals(): sender_task.cancel()
                print("⚠️ Connection lost. Retrying in 2s...")
                await asyncio.sleep(2)
            except Exception as e:
                if 'sender_task' in locals(): sender_task.cancel()
                print(f"[ERROR] {e}")
                await asyncio.sleep(2)

    async def sender_loop(self, websocket):
        """Reads from TelemetryOutput queue and sends via websocket."""
        q = TelemetryOutput.get_queue()
        while True:
            try:
                # Non-blocking check
                if not q.empty():
                    msg = q.get_nowait()
                    await websocket.send(msg)
                else:
                    await asyncio.sleep(0.05) # Yield to avoid hogging CPU
            except Exception as e:
                print(f"Telemetry Send Error: {e}")
                await asyncio.sleep(1)