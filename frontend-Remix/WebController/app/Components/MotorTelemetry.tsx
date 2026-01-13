import React, { useEffect, useState } from 'react';

interface MotorTelemetryProps {
    data: {
        V: number;
        I: number; // Assumed in mA based on user request
        P: number;
    } | null;
}

const MotorTelemetry: React.FC<MotorTelemetryProps> = ({ data }) => {
    const [isCharging, setIsCharging] = useState(false);

    // Convert raw mA to Amps for calculations and display if needed
    // If data.I is mA:
    // -0.1A = -100mA
    // 0.0A = 0mA
    const currentAmps = data ? data.I / 1000 : 0;

    useEffect(() => {
        if (!data) return;

        // Hysteresis Logic (based on Amps)
        // Enter Charging: < -0.1A
        // Exit Charging: > 0.0A
        if (isCharging) {
            if (currentAmps > 0.0) {
                setIsCharging(false);
            }
        } else {
            if (currentAmps < -0.1) {
                setIsCharging(true);
            }
        }
    }, [currentAmps, isCharging, data]);

    if (!data) return null;

    const { V, P } = data;
    const absAmps = Math.abs(currentAmps);

    // DJI-inspired Top Bar / OSD Style
    // Usually clean white text with icons, semi-transparent black pill background
    return (
        <div className="select-none">
            <div className="flex items-center gap-1.5 p-1.5 pl-3 pr-4 bg-black/60 backdrop-blur-md rounded-full border border-white/10 shadow-lg text-white font-sans text-sm">

                {/* Voltage Section */}
                <div className="flex items-center gap-1.5 border-r border-white/20 pr-3">
                    <svg className={`w-4 h-4 ${V < 11.0 ? "text-red-500 animate-pulse" : "text-emerald-400"}`} fill="currentColor" viewBox="0 0 24 24">
                        <path d="M11.67 3.87 9.9 11h4l-1.77 7.13 5.77-7.13h-4l1.77-7.13z" />
                    </svg>
                    <div>
                        <span className="font-bold text-[30px]">{V.toFixed(1)}</span>
                        <span className="text-[30px] ml-0.5 text-white/70">V</span>
                    </div>
                </div>

                {/* Current Section / Status */}
                <div className="flex items-center gap-1.5 border-r border-white/20 pr-3 pl-1">
                    {/* CHARGING STATUS */}
                    {isCharging ? (
                        <div className="flex items-center gap-1.5">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                            </span>
                            <span className="font-bold text-[30px] text-emerald-400 tracking-wider">CHG</span>
                        </div>
                    ) : (
                        // DISCHARGING / IDLE STATUS
                        <div className="flex items-center gap-1">
                            <span className="text-white/70 font-bold text-[30px]">CURR</span>
                        </div>
                    )}

                    <div className="flex items-baseline">
                        <span className={`font-bold text-[30px] ${isCharging ? "text-emerald-400" : "text-white"}`}>
                            {absAmps.toFixed(2)}
                        </span>
                        <span className="text-[30px] ml-0.5 text-white/70">A</span>
                    </div>
                </div>

                {/* Power Section */}
                <div className="flex items-center gap-1.5 pl-1">
                    <span className="text-[30px]  px-1 rounded text-white/90 font-bold">PWR</span>
                    <div>
                        <span className="font-bold text-[30px]">{P.toFixed(0)}</span>
                        <span className="text-[30px] ml-0.5 text-white/70">W</span>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default MotorTelemetry;
