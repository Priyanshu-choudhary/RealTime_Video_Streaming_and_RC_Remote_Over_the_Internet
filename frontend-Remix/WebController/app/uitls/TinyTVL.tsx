const TTP_MAX_FRAME = 256
const TTP_STX = 0x02
// const TTP_FRAME_TYPE_RC = 0x01

const buffer = new ArrayBuffer(TTP_MAX_FRAME);
const view = new DataView(buffer);

let pos = 0;


export function Init(type: number) {
    pos = 0;
    view.setUint8(pos++, TTP_STX);  // header 

    // view.setUint8(pos,xx); //leave the length of all TVL's Frames 
    pos++;
    view.setUint8(pos++, type); // type
    return view;
}

export function getByteSize(num = 0) {
    if (num <= 0xFF) return 1;       // Fits in 8 bits
    if (num <= 0xFFFF) return 2;     // Fits in 16 bits
    if (num <= 0xFFFFFFFF) return 4; // Fits in 32 bits
    return 8;                        // Needs 64 bits (BigInt or Float)
}

// 1. Revert to simple Integer TVL
export function addTVL(type = 1, data = 0) {
    const size = getByteSize(data);
    view.setUint8(pos++, type)
    view.setUint8(pos++, size)

    if (size === 1) {
        view.setUint8(pos, data);
    } else if (size === 2) {
        view.setUint16(pos, data, true); // Writes 2 bytes
    } else if (size === 4) {
        view.setUint32(pos, data, true); // Writes 4 bytes
    }
    pos = pos + size;
}

export function addTimestampTVL(data: number) {
    view.setUint8(pos++, 100); // ID
    view.setUint8(pos++, 4);   // Force Size 4
    view.setUint32(pos, data >>> 0, true);
    pos += 4;
}

export function addFloatTVL(type: number, data: number) {
    view.setUint8(pos++, type);
    view.setUint8(pos++, 4); // Floats are always 4 bytes
    view.setFloat32(pos, data, true); // Little endian
    pos += 4;
}
export function sealFrame() {
    //length
    const lengthOfData = pos - 2;
    view.setUint8(1, lengthOfData);


    let crc = 0;
    for (let i = 2; i < pos; i++) {
        crc ^= view.getUint8(i);
    }
    //xor checksum added bit at the end 
    // 3. Add CRC at the end
    view.setUint8(pos++, crc);

    return buffer.slice(0, pos);
}

// Init();
// addTVL(1,99);
// const finalFrame = sealFrame();

// // To see your beautiful binary work in hex:
// console.log(new Uint8Array(finalFrame));

const bufferRX = new ArrayBuffer(TTP_MAX_FRAME);

let posRX = 0;
export function decode(viewRX: DataView): DataView {

    const sizeOfTVL = viewRX.getUint8(4)
    const tvl = new DataView(buffer);
    tvl.setUint8(0, viewRX.getUint8(5))
    tvl.setUint8(1, viewRX.getUint8(6))
    return tvl;
}
