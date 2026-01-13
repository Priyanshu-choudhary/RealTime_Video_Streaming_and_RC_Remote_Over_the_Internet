import React, { useState, useEffect, useRef } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface TelemetryGraphsProps {
    data: {
        V: number;
        I: number; // mA
        P: number;
    } | null;
}

// Configuration for each graph
// Duration in seconds vs Update Interval in ms
// Aim for ~300 points for smooth but performant graph
// Voltage: 10 min = 600s. Interval 2000ms (2s) -> 300 pts.
// Current: 1 min = 60s. Interval 200ms -> 300 pts.
// Power: 30s. Interval 100ms -> 300 pts.

const MAX_POINTS = 300;

// Fix type for formatter: val can be number or undefined/string depending on library types, but we expect number from dataKey
const formatTooltipInfo = (val: any, unit: string, title: string) => {
    if (typeof val === 'number') return [val.toFixed(2) + unit, title];
    return [val, title];
};

const TelemetryGraphs: React.FC<TelemetryGraphsProps> = ({ data }) => {
    // We use refs to hold the latest data to be sampled by intervals
    const latestDataRef = useRef(data);

    // Update ref when data changes
    useEffect(() => {
        latestDataRef.current = data;
    }, [data]);

    // State for chart data
    const [dataV, setDataV] = useState<{ time: number; val: number }[]>([]);
    const [dataI, setDataI] = useState<{ time: number; val: number }[]>([]);
    const [dataP, setDataP] = useState<{ time: number; val: number }[]>([]);

    // Timers
    useEffect(() => {
        // Voltage Timer (2s interval)
        const intervalV = setInterval(() => {
            if (!latestDataRef.current) return;
            setDataV(prev => {
                const newVal = { time: Date.now(), val: latestDataRef.current!.V };
                const newArr = [...prev, newVal];
                return newArr.length > MAX_POINTS ? newArr.slice(-MAX_POINTS) : newArr;
            });
        }, 2000);

        // Current Timer (200ms interval)
        const intervalI = setInterval(() => {
            if (!latestDataRef.current) return;
            setDataI(prev => {
                // Convert mA to A for display
                const amps = latestDataRef.current!.I / 1000;
                const newVal = { time: Date.now(), val: amps };
                const newArr = [...prev, newVal];
                return newArr.length > MAX_POINTS ? newArr.slice(-MAX_POINTS) : newArr;
            });
        }, 200);

        // Power Timer (100ms interval)
        const intervalP = setInterval(() => {
            if (!latestDataRef.current) return;
            setDataP(prev => {
                const newVal = { time: Date.now(), val: latestDataRef.current!.P };
                const newArr = [...prev, newVal];
                return newArr.length > MAX_POINTS ? newArr.slice(-MAX_POINTS) : newArr;
            });
        }, 100);

        return () => {
            clearInterval(intervalV);
            clearInterval(intervalI);
            clearInterval(intervalP);
        };
    }, []);

    const handleClear = () => {
        setDataV([]);
        setDataI([]);
        setDataP([]);
    };

    return (
        <div className="flex flex-col gap-4">
            <div className="flex justify-between items-center">
                <h2 className="text-slate-200 font-bold text-sm">Telemetry History</h2>
                <button
                    onClick={handleClear}
                    className="text-xs text-slate-500 hover:text-white transition-colors flex items-center gap-1"
                >
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                    Clear
                </button>
            </div>

            <MiniChart
                title="Voltage"
                data={dataV}
                color="#3b82f6" // blue-500
                unit="V"
                durationLabel="10m"
                domain={[9.8, 13]}
            />

            <MiniChart
                title="Current"
                data={dataI}
                color="#10b981" // emerald-500
                unit="A"
                durationLabel="1m"
            />

            <MiniChart
                title="Power"
                data={dataP}
                color="#f59e0b" // amber-500
                unit="W"
                durationLabel="30s"
            />
        </div>
    );
};

// Reusable Chart Component (Moved Outside to prevent re-mounting)
const MiniChart = React.memo(({
    title,
    data,
    color,
    unit,
    durationLabel,
    domain // Allow custom domain override
}: {
    title: string;
    data: any[];
    color: string;
    unit: string;
    durationLabel: string;
    domain?: [number, number];
}) => (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 flex flex-col h-[180px]">
        <div className="flex justify-between items-baseline mb-2">
            <h3 className="text-slate-400 text-xs font-bold uppercase tracking-wider">{title}</h3>
            <div className="flex gap-2 text-[10px] text-slate-500 font-mono">
                <span>{durationLabel} History</span>
                <span className={`${color} font-bold`}>
                    {data.length > 0 ? data[data.length - 1].val.toFixed(2) : "---"} {unit}
                </span>
            </div>
        </div>
        <div className="flex-1 min-h-0" style={{ minHeight: 120 }}>
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data}>
                    <defs>
                        <linearGradient id={`grad${title}`} x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                            <stop offset="95%" stopColor={color} stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                    <XAxis dataKey="time" hide />
                    <YAxis
                        hide
                        domain={domain || ['auto', 'auto']}
                        tickFormatter={(v) => v.toFixed(1)}
                    />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '12px' }}
                        itemStyle={{ color: '#cbd5e1' }}
                        labelFormatter={() => ''}
                        formatter={(val) => formatTooltipInfo(val, unit, title)}
                    />
                    <Area
                        type="monotone"
                        dataKey="val"
                        stroke={color}
                        fillOpacity={1}
                        fill={`url(#grad${title})`}
                        isAnimationActive={false}
                        strokeWidth={2}
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    </div>
));

export default TelemetryGraphs;
