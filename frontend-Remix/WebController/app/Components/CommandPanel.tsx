import React, { useState } from "react";
import { Card } from "./DashboardUI";

interface CommandUplinkProps {
    connection: boolean;
    isVehicleOffline: boolean;
    send: (data: string | ArrayBuffer) => void;
    onLog: (msg: string, source: 'TX' | 'RX') => void;
}

export function CommandUplink({ connection, isVehicleOffline, send, onLog }: CommandUplinkProps) {
    const [cmd, setCmd] = useState("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!cmd.trim()) return;

        if (connection && !isVehicleOffline) {
            send(cmd);
            onLog(cmd, 'TX');
            setCmd("");
        } else {
            // Maybe show error toast, for now just log
            console.warn("Cannot send: Offline");
        }
    };

    return (
        <Card title="Command Uplink">
            <form onSubmit={handleSubmit} className="p-4 flex gap-2">
                <input
                    type="text"
                    value={cmd}
                    onChange={(e) => setCmd(e.target.value)}
                    placeholder="Enter command..."
                    disabled={!connection || isVehicleOffline}
                    className="flex-1 bg-slate-950 border border-slate-700 rounded px-3 py-2 text-sm text-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none disabled:opacity-50"
                />
                <button
                    type="submit"
                    disabled={!connection || isVehicleOffline}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded text-sm font-bold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    SEND
                </button>
            </form>
        </Card>
    );
}

export function OutputLog({ logs }: { logs: { time: string, msg: string, source: 'TX' | 'RX' }[] }) {
    const bottomRef = React.useRef<HTMLDivElement>(null);

    React.useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [logs]);

    return (
        <Card title="System Log" className="flex flex-col h-[200px]">
            <div className="flex-1 overflow-y-auto p-2 space-y-1 font-mono text-xs">
                {logs.length === 0 && <div className="text-slate-600 italic text-center py-4">No logs yet...</div>}
                {logs.map((log, i) => (
                    <div key={i} className={`flex gap-2 ${log.source === 'TX' ? 'text-indigo-400' : 'text-emerald-400'}`}>
                        <span className="text-slate-600 shrink-0">[{log.time}]</span>
                        <span className="font-bold shrink-0">{log.source}&gt;</span>
                        <span className="text-slate-300 break-all">{log.msg}</span>
                    </div>
                ))}
                <div ref={bottomRef} />
            </div>
        </Card>
    );
}
