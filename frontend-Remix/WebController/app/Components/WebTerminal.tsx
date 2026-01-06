import { useEffect, useRef } from "react";
import { Card } from "./DashboardUI";
// Note: Real implementation likely used 'xterm' and 'xterm-addon-fit'.
// Restoring a basic mocked terminal interface unless I load those libraries.
// I will assume a simple text area for now to prevent build errors if packages are missing, 
// but try to mimic the UI.

interface WebTerminalProps {
    connection: boolean;
    send: (data: string | ArrayBuffer) => void;
    logs: { time: string, msg: string, source: 'TX' | 'RX' }[];
    isRCOn: boolean;
    onLog: (msg: string, source: 'TX' | 'RX') => void;
}

export default function WebTerminal({ connection, logs }: WebTerminalProps) {
    const terminalRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (terminalRef.current) {
            terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
        }
    }, [logs]);

    return (
        <Card title="Web Terminal" className="h-[400px] flex flex-col font-mono text-sm">
            <div ref={terminalRef} className="flex-1 bg-black p-4 overflow-y-auto text-green-500 space-y-1">
                <div className="text-slate-500"># Connected to Remote Shell</div>
                {logs.map((l, i) => (
                    <div key={i}>
                        <span className="text-slate-600">[{l.time}]</span>
                        {l.source === 'TX' ? <span className="text-blue-500"> $ </span> : <span className="text-purple-500"> &gt; </span>}
                        {l.msg}
                    </div>
                ))}
            </div>
            {/* Input would go here, simplified for recovery */}
            <div className="bg-slate-900 p-2 border-t border-slate-700">
                <span className="text-slate-500 text-xs">Terminal input disabled in recovery mode.</span>
            </div>
        </Card>
    );
}
