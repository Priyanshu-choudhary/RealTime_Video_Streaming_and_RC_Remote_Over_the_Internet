import React from "react";

// --- Card ---
export function Card({ title, children, className = "" }: { title?: string, children: React.ReactNode, className?: string }) {
    return (
        <div className={`bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden backdrop-blur-sm ${className}`}>
            {title && (
                <div className="bg-slate-900/50 p-4 border-b border-slate-800">
                    <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider">{title}</h3>
                </div>
            )}
            <div className="">{children}</div>
        </div>
    );
}

// --- StatusBadge ---
export function StatusBadge({ active, label }: { active: boolean, label: string }) {
    return (
        <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold border ${active
            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
            : "bg-red-500/10 text-red-400 border-red-500/20"
            }`}>
            <div className={`w-2 h-2 rounded-full ${active ? "bg-emerald-500 animate-pulse" : "bg-red-500"}`} />
            {label}
        </div>
    );
}

// --- ModeBadge ---
export function ModeBadge({ mode }: { mode: string }) {
    let colors = "bg-slate-500/10 text-slate-400 border-slate-500/20"; // Manual/Default
    let dotColor = "bg-slate-500";

    if (mode === "AUTO") {
        colors = "bg-indigo-500/10 text-indigo-400 border-indigo-500/20";
        dotColor = "bg-indigo-500 animate-pulse";
    } else if (mode === "SEMI-AUTO") {
        colors = "bg-amber-500/10 text-amber-400 border-amber-500/20";
        dotColor = "bg-amber-500";
    }

    return (
        <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold border ${colors}`}>
            <div className={`w-2 h-2 rounded-full ${dotColor}`} />
            {mode}
        </div>
    );
}

// --- MetricRow ---
export function MetricRow({ label, value, unit }: { label: string, value: string | number, unit?: string }) {
    return (
        <div className="flex justify-between items-center py-2 border-b border-slate-800 last:border-0 px-4">
            <span className="text-slate-400 text-sm">{label}</span>
            <span className="font-mono text-slate-200">
                {value}
                {unit && <span className="text-slate-500 text-xs ml-1">{unit}</span>}
            </span>
        </div>
    );
}

// --- ProgressBar ---
export function ProgressBar({ label, value, max = 2000, min = 1000, color = "bg-indigo-500" }: { label: string, value: number, max?: number, min?: number, color?: string }) {
    const percent = Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));

    return (
        <div className="px-4">
            <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400">{label}</span>
                <span className="font-mono text-slate-300">{value}</span>
            </div>
            <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div
                    className={`h-full rounded-full transition-all duration-75 ${color}`}
                    style={{ width: `${percent}%` }}
                />
            </div>
        </div>
    );
}

// --- JoystickVisualizer ---
export function JoystickVisualizer({ x, y }: { x: number, y: number }) {
    // Map 1000-2000 to -1 to 1
    const map = (v: number) => ((v - 1500) / 500);
    const xPos = map(x) * 80; // max 40px offset
    const yPos = map(y) * -80; // Invert Y for screen coords

    return (
        <div className="w-40 h-40 rounded-full border border-slate-700 bg-slate-800/50 relative mx-auto flex items-center justify-center">
            {/* Crosshairs */}
            <div className="absolute w-full h-[1px] bg-slate-700/50" />
            <div className="absolute h-full w-[1px] bg-slate-700/50" />

            {/* Stick */}
            <div
                className="w-5 h-5 rounded-full bg-indigo-500/20 border border-indigo-500 shadow-[0_0_15px_rgba(99,102,241,0.3)] transition-transform duration-75 flex items-center justify-center"
                style={{ transform: `translate(${xPos}px, ${yPos}px)` }}
            >
                <div className="w-2 h-2 bg-indigo-400 rounded-full" />
            </div>
        </div>
    );
}
