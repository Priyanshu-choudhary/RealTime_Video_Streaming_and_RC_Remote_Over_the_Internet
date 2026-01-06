import { Card } from "~/Components/DashboardUI";

interface ConfigState {
    P: number;
    I: number;
    D: number;
}

export default function ConfigDashboard({ config, setConfig, handleSend }: { config: ConfigState; setConfig: React.Dispatch<React.SetStateAction<ConfigState>>; handleSend: () => void }) {

    // Using slightly more realistic default PID values for a drone/robot

    const handleChange = (name: keyof ConfigState, value: string) => {
        // Allow decimals
        const num = parseFloat(value);
        if (!isNaN(num)) {
            setConfig(prev => ({ ...prev, [name]: num }));
        } else if (value === '') {
            // Handle empty input for typing experience, though simpler to just ignore
            // or keep prev value. For now, strict:
            // setConfig(prev => ({ ...prev, [name]: 0 })); 
            // Actually, letting it be partial controlled input logic is complex without separate state.
            // We'll stick to direct number input.
        }
    };


    return (
        <Card title="PID Tuner">
            <div className="grid grid-cols-3 gap-4 p-4">
                {(['P', 'I', 'D'] as const).map((key) => (
                    <div key={key} className="flex flex-col gap-2">
                        <label className="text-slate-400 text-xs font-bold uppercase">{key} Gain</label>
                        <input
                            type="number"
                            step="0.001"
                            value={config[key]}
                            onChange={(e) => handleChange(key, e.target.value)}
                            className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white focus:border-indigo-500 outline-none text-sm font-mono"
                        />
                    </div>
                ))}
            </div>
            <div className="px-4 pb-4">
                <button
                    onClick={handleSend}
                    className="w-full py-2 rounded bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm transition-colors shadow-lg shadow-indigo-500/20"
                >
                    UPDATE CONFIG
                </button>
            </div>
        </Card>
    );
}
