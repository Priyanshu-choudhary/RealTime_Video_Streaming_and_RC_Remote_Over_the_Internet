import asyncio
import websockets
from struct import unpack


class RCData:
    """Simple container to allow dot-access (Throttle, Roll, Aux1, Aux2)."""
    def __init__(self, throttle, roll, aux1, aux2):
        self.Throttle = throttle
        self.Roll = roll
        self.Aux1 = aux1
        self.Aux2 = aux2

    def __repr__(self):
        return f"RCData(T={self.Throttle}, R={self.Roll}, A1={self.Aux1}, A2={self.Aux2})"


class WebSocketDecoder:
    def __init__(self, uri):
        self.uri = uri
        self.websocket = None
        self.last_decoded = None  # store last decoded RCData

    async def connect(self):
        """Connect to the websocket server."""
        self.websocket = await websockets.connect(self.uri)
        print(f"Connected to {self.uri}")

    def decode(self, msg: bytes):
        """Decode 6-byte binary packet into RCData object."""
        if len(msg) != 6:
            return None

        view = memoryview(msg)

        # First 3 bytes → throttle + roll
        word1 = unpack('>H', view[:2])[0]
        throttle = (word1 >> 6) + 1000
        roll_high = (word1 & 0x3F) << 4
        roll_low = (view[2] >> 4) & 0x0F
        roll = (roll_high | roll_low) + 1000

        # Next 3 bytes → aux1 + aux2
        word2 = unpack('>H', view[3:5])[0]
        aux1 = (word2 >> 6) + 1000
        aux2_high = (word2 & 0x3F) << 4
        aux2_low = (view[5] >> 4) & 0x0F
        aux2 = (aux2_high | aux2_low) + 1000

        return RCData(throttle, roll, aux1, aux2)

    async def listen(self):
        """Keep listening and decoding packets."""
        try:
            while True:
                msg = await self.websocket.recv()
                if isinstance(msg, bytes):
                    decoded = self.decode(msg)
                    if decoded:
                        self.last_decoded = decoded
  #                      print("Decoded:", decoded)
                else:
                    print(f"Unexpected text message: {msg}")
        except websockets.ConnectionClosed as e:
            print(f"Connection closed: {e.code}, {e.reason}")
        except Exception as e:
            print(f"Listen error: {e}")

    def get_last_data(self):
        """Getter for latest decoded RCData."""
        return self.last_decoded
