


TTP_STX = 0x02
TTP_MAX_FRAME = 256
TTP_FRAME_TYPE_RC = 0x01 # New: Define the RC Frame Type here

# =====================================================
# ====================== TX ===========================
# =====================================================

class TinyTLVTx:
    def __init__(self):
        self.buf = bytearray(TTP_MAX_FRAME)
        self.pos = 0
        self.type = 0

    def begin(self, t: int):
        self.pos = 0
        self.type = t

        # Reserve STX + LEN later
        self.buf[0] = 0
        self.buf[1] = 0
        self.buf[2] = self.type

        self.pos = 3

    def addTLV(self, id_: int, length: int, data: bytes):
        self.buf[self.pos] = id_
        self.pos += 1

        self.buf[self.pos] = length
        self.pos += 1

        for b in data:
            self.buf[self.pos] = b
            self.pos += 1

    def end(self) -> bytes:
        """Returns the final frame as bytes."""
        length = self.pos - 2   # TYPE + TLVs
        chk = 0

        out = bytearray(3 + length)

        out[0] = TTP_STX
        out[1] = length

        # copy TYPE+TLVs
        for i in range(length):
            v = self.buf[2 + i]
            out[2 + i] = v
            chk ^= v

        # checksum
        out[2 + length] = chk

        return bytes(out)
class TinyTLVRx:
    WAIT_STX = 0
    READ_LEN = 1
    READ_DATA = 2

    def __init__(self):
        self.buf = bytearray(TTP_MAX_FRAME)
        self.reset()

    def reset(self):
        self.pos = 0
        self.expected = 0
        self.state = TinyTLVRx.WAIT_STX
        self.frame_ready = 0
        self.tlv_pos = 0

    def feed(self, b: int) -> int:
        """Feed ONE BYTE. Returns 1 when a full frame is ready."""
        if self.state == TinyTLVRx.WAIT_STX:
            if b == TTP_STX:
                self.state = TinyTLVRx.READ_LEN

        elif self.state == TinyTLVRx.READ_LEN:
            self.expected = b
            self.pos = 0
            self.state = TinyTLVRx.READ_DATA

        elif self.state == TinyTLVRx.READ_DATA:
            self.buf[self.pos] = b
            self.pos += 1

            if self.pos >= self.expected + 1:  # +1 includes checksum
                # check XOR-sum
                calc = 0
                for i in range(self.expected):
                    calc ^= self.buf[i]

                chk = self.buf[self.expected]

                if chk == calc:
                    self.frame_ready = 1

                self.state = TinyTLVRx.WAIT_STX
                return self.frame_ready

        return 0

    def isComplete(self) -> int:
        return self.frame_ready

    def getType(self) -> int:
        return self.buf[0]  # same as C++

    def beginTLV(self):
        self.tlv_pos = 1  # TYPE is at index 0

    def nextTLV(self):
        """Returns (id, length, data_bytes) OR None if done."""
        if self.tlv_pos >= self.expected:
            self.frame_ready = 0
            return None

        id_ = self.buf[self.tlv_pos]
        self.tlv_pos += 1

        length = self.buf[self.tlv_pos]
        self.tlv_pos += 1

        data = bytes(self.buf[self.tlv_pos:self.tlv_pos + length])

        self.tlv_pos += length

        return id_, length, data
