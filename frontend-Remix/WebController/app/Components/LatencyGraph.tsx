import { useEffect, useRef } from "react";

export default function LatencyGraph({ currentLatency }: { currentLatency: number }) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const historyRef = useRef<number[]>(new Array(60).fill(0));

    useEffect(() => {
        historyRef.current.push(currentLatency);
        if (historyRef.current.length > 60) historyRef.current.shift();

        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        // Clear
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw
        ctx.beginPath();
        ctx.strokeStyle = "#10b981"; // Emerald-500
        ctx.lineWidth = 2;

        const step = canvas.width / 60;

        // Find limits for scaling
        const max = Math.max(150, ...historyRef.current);
        const min = 0;
        const range = max - min;

        historyRef.current.forEach((val, i) => {
            const x = i * step;
            const y = canvas.height - ((val - min) / range) * canvas.height;

            if (val > 200) ctx.strokeStyle = "#f59e0b"; // Amber if high

            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });

        ctx.stroke();

        // Max Latency Text
        if (max > 0) {
            ctx.fillStyle = max > 200 ? "#ef4444" : "#94a3b8"; // Red if high, else Slate-400
            ctx.font = "15px monospace";
            ctx.fillText(`Max: ${max}ms`, canvas.width - 65, 12);
        }

    }, [currentLatency]);

    return (
        <canvas ref={canvasRef} width={280} height={50} className="w-full h-[50px] opacity-80" />
    );
}
