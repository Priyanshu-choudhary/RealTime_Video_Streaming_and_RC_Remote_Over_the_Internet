import { Init, addFloatTVL, sealFrame } from "~/uitls/TinyTVL";

interface ConfigState {
    P: number;
    I: number;
    D: number;
}

export default function makeConfig_Packets(config: ConfigState) {
    const TTP_FRAME_TYPE_CONFIG = 0x02;
    Init(TTP_FRAME_TYPE_CONFIG);
    addFloatTVL(1, config.P);
    addFloatTVL(2, config.I);
    addFloatTVL(3, config.D);

    const finalFrame = sealFrame();
    return finalFrame;
}
