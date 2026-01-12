# rc_ws_client.py
import asyncio
import websockets
import struct
import time
from typing import Dict, Any
from tinytlvx import TinyTLVRx, TTP_FRAME_TYPE_RC, TTP_FRAME_TYPE_CONFIG

# =========================
# CHANNEL DEFINITIONS
# =========================

RC_CHANNELS = {
    0: "Roll",
    1: "Pitch",
    4: "Aux1",
    5: "Aux2",
    100: "timestamp"
}

CONFIG = {
    1: "Kp",
    2: "Ki",
    3: "Kd",
}

# =========================
# RC DECODER
# =========================

class RCDataDecoder:
    def __init__(self, ws_uri, loop):
        self.ws_uri = ws_uri
        self.loop = loop
        self.rx = TinyTLVRx()
        self.latest_data = {}
        self.loop = asyncio.get_event_loop()

    def get_latest_data(self) -> Dict[str, Any]:
        return self.latest_data

    def decode_rc_data(self) -> Dict[str, Any]:
        frame_type = self.rx.getType()
        decoded = {}

        if frame_type == TTP_FRAME_TYPE_CONFIG:
            self.rx.beginTLV()
            while True:
                tlv = self.rx.nextTLV()
                if tlv is None:
                    break

                ch_id, length, data = tlv
                if length == 4:
                    value = struct.unpack("<f", data)[0]
                elif length == 2:
                    value = struct.unpack("<H", data)[0]
                else:
                    continue

                decoded[CONFIG.get(ch_id, f"CFG_{ch_id}")] = value

            decoded["_type"] = "CONFIG"
            return decoded

        elif frame_type == TTP_FRAME_TYPE_RC:
            self.rx.beginTLV()
            while True:
                tlv = self.rx.nextTLV()
                if tlv is None:
                    break

                ch_id, length, data = tlv

                if ch_id == 100 and length == 4:
                    # Timestamp is a Uint32
                    decoded["timestamp"] = struct.unpack('<I', data)[0]
                    
                if length == 2:
                    value = struct.unpack("<H", data)[0]
                    decoded[RC_CHANNELS.get(ch_id, f"CH_{ch_id}")] = value

            decoded["_type"] = "RC"
            return decoded

        return {}

    # =========================
    # SENDER LOOP
    # =========================
    async def sender_loop(self, websocket):
        """
        Periodically sends telemetry back to server.
        Replace payload with your real telemetry.
        """
        while True:
            try:
                payload = {
                    "heartbeat": True,
                    "ts":  int(time.time() * 1000) & 0xFFFFFFFF
                }
                await websocket.send(struct.pack("<I", payload["ts"]))
                await asyncio.sleep(0.1)
            except Exception as e:
                print("[SENDER ERROR]", e)
                return

    # =========================
    # MAIN RECEIVER LOOP
    # =========================
    async def run(self):
        while True:
            try:
                async with websockets.connect(self.ws_uri) as websocket:
                    print("🔗 Connected to", self.ws_uri)
                    self.rx.reset()

                    # START SENDER TASK (Python 3.6 safe)
                    sender_task = self.loop.create_task(
                        self.sender_loop(websocket)
                    )

                    try:
                        while True:
                            message = await websocket.recv()

                            arrival_ts = int(time.time() * 1000) & 0xFFFFFFFF

                            if isinstance(message, str):
                                continue

                            for b in message:
                                if self.rx.feed(b):
                                    decoded = self.decode_rc_data()
                                    if decoded:
                                        decoded["arrival_ts"] = arrival_ts
                                        self.latest_data = decoded
                                        # print(decoded)

                    except websockets.exceptions.ConnectionClosed:
                        print("⚠️ WebSocket closed")
                        sender_task.cancel()

            except Exception as e:
                print("[ERROR]", e)
                await asyncio.sleep(2)

# =========================
# ENTRY POINT
# =========================

def main():
    ws_uri = "ws://yadiec2.freedynamicdns.net:8080/ws"
    decoder = RCDataDecoder(ws_uri)

    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_until_complete(decoder.run())

if __name__ == "__main__":
    main()
