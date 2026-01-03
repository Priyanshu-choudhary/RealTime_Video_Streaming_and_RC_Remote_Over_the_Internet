import asyncio
import websockets
import sys

from tinytlvx import TinyTLVRx  

WS_URI = "ws://localhost:8080/ws"

rx = TinyTLVRx()   # <-- THE REAL DECODER INSTANCE


async def receive_data():
    print(f"Connecting to: {WS_URI}")

    while True:
        try:
            async with websockets.connect(WS_URI) as websocket:
                print(f"### Connected to {WS_URI} ###")
                print("Waiting for TinyTLV frames...\n")

                while True:
                    message = await websocket.recv()

                    # ---------- MUST BE BYTES ----------
                    if isinstance(message, str):
                        # Text message -> ignore
                        print("[TEXT] ", message)
                        continue

                    print(f"\n--- Binary Frame Received ({len(message)} bytes) ---")
                    print("HEX:", " ".join(f"{b:02X}" for b in message))

                    # ----------- FEED BYTES TO DECODER ------------
                    for byte in message:
                        if rx.feed(byte):     # frame complete
                            print(">>> FRAME OK")

                            t = rx.getType()
                            print("TYPE =", t)

                            rx.beginTLV()

                            while True:
                                tlv = rx.nextTLV()
                                if tlv is None:
                                    break

                                id, length, data = tlv
                                if length == 2:
                                    value = data[0] | (data[1] << 8)
                                    print(id, value)


                            print("------------------------------------")

        except websockets.exceptions.ConnectionClosedError:
            print("Connection lost. Reconnecting...")
            await asyncio.sleep(2)
        except Exception as e:
            print(f"[ERROR] {e}")
            await asyncio.sleep(2)



if __name__ == "__main__":
    try:
        asyncio.run(receive_data())
    except KeyboardInterrupt:
        print("Client stopped.")
