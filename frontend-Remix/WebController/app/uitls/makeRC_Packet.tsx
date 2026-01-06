import { Init, addTVL, decode, sealFrame, addTimestampTVL } from "~/uitls/TinyTVL";

export default function makeRC_Packet(uiState: any) {
    // 0 to 2^32-1
    const localNow = Date.now();
    const localLower = (Date.now() & 0xFFFFFFFF) >>> 0; // The >>> 0 makes it unsigned
    const TTP_FRAME_TYPE_RC = 0x01
    Init(TTP_FRAME_TYPE_RC);
    addTVL(1, uiState.throttle);
    addTVL(0, uiState.roll);
    addTVL(3, uiState.aux1);
    addTVL(4, uiState.aux2);
    addTimestampTVL(localLower); //default id is 100
    const finalFrame = sealFrame();
    return finalFrame;
}
