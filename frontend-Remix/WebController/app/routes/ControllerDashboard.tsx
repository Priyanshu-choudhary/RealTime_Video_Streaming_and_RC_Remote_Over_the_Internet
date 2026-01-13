import { useEffect, useState, useRef } from "react";
import { useWebSocket } from "~/uitls/websockets.clint";
import useButtonInput from "~/uitls/UseButtonInput";
import makeRC_Packet from "~/uitls/makeRC_Packet";
import { CameraView } from "~/uitls/CameraView";
import { useHealth } from "~/uitls/HealthCheck";
import LatencyGraph from "~/Components/LatencyGraph";
import makeConfig_Packets from "~/uitls/makeConfig_Packets";
// Imported Components
import { Card, StatusBadge, MetricRow, ProgressBar, JoystickVisualizer, ModeBadge } from "~/Components/DashboardUI";
import WebTerminal from "~/Components/WebTerminal";
import { CommandUplink, OutputLog } from "~/Components/CommandPanel";
import ConfigDashboard from "~/Components/ConfigDashboard";

import DynamicJsonGraph from "~/Components/TelemetryGraph";
import MotorTelemetry from "~/Components/MotorTelemetry";
import TelemetryGraphs from "~/Components/TelemetryGraphs";


interface ConfigState {
  P: number;
  I: number;
  D: number;
}

export default function ControllerDashboard() {
  const WS_ENDPOINT = import.meta.env.VITE_WS_ENDPOINT;
  /* eslint-disable react-hooks/exhaustive-deps */
  const { send, connection, reconnect, lastMessage } = useWebSocket(`ws://${WS_ENDPOINT}:8080/ws`);
  const [videoKey, setVideoKey] = useState(0);
  const { uiState, speed, handleChange, mode } = useButtonInput();
  const { health } = useHealth();
  const [logs, setLogs] = useState<{ time: string; msg: string; source: 'TX' | 'RX' }[]>([]);
  const [config, setConfig] = useState<ConfigState>({ P: 1.50, I: 0.3, D: 0.3 });

  // Logic for Vehicle Offline
  const lastBeat = Math.floor((Date.now() - (health?.last_message_time || Date.now())) / 1000);
  const isVehicleOffline = lastBeat > 5;

  const [isTerminalMode, setIsTerminalMode] = useState(false);
  const [isRCOn, setIsRCOn] = useState(true);
  const [motorTelemetry, setMotorTelemetry] = useState<{
    V: number
    I: number
    P: number
  } | null>(null);

  // Optimization: Store latest telemetry in ref to throttle re-renders
  const latestTelemetryRef = useRef<{ V: number; I: number; P: number } | null>(null);

  // Performance Controls State
  const [enableTelemetry, setEnableTelemetry] = useState(true);
  const [enableGraphs, setEnableGraphs] = useState(true);

  // Helper to add logs from child components
  const addLog = (msg: string, source: 'TX' | 'RX') => {
    const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });
    setLogs(prev => [...prev, { time, msg, source }].slice(-20));
  };

  // Handle Incoming Messages
  useEffect(() => {
    if (!lastMessage) return;

    const time = new Date().toLocaleTimeString('en-US', {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit"
    });

    let parsed: any = null;

    // 1️⃣ Normalize to object if possible
    if (typeof lastMessage === "string") {
      try {
        parsed = JSON.parse(lastMessage);
      } catch {
        // Not JSON, treat as plain string
        setLogs(prev => {
          const newLogs = [...prev, { time, msg: lastMessage, source: 'RX' as const }];
          return newLogs.slice(-20);
        });
        return;
      }
    } else if (typeof lastMessage === "object") {
      parsed = lastMessage;
    }

    // 2️⃣ Detect motorTelemetry JSON (shape check)
    if (
      parsed &&
      typeof parsed === "object" &&
      parsed.motorTelemetry &&
      typeof parsed.motorTelemetry.V === "number" &&
      typeof parsed.motorTelemetry.I === "number" &&
      typeof parsed.motorTelemetry.P === "number"
    ) {
      const { V, I, P } = parsed.motorTelemetry;

      // ✅ Update telemetry UI
      setMotorTelemetry({ V, I, P });

      // ❌ DO NOT log this message
      return;
    }

    // 3️⃣ Everything else → logs
    if (parsed) {
      setLogs(prev => {
        const newLogs = [
          ...prev,
          { time, msg: JSON.stringify(parsed), source: 'RX' as const }
        ];
        return newLogs.slice(-20);
      });
    }

  }, [lastMessage]);

  // Throttled UI Update Loop (10Hz)
  useEffect(() => {
    const interval = setInterval(() => {
      if (latestTelemetryRef.current && enableTelemetry) {
        setMotorTelemetry(latestTelemetryRef.current);
        // Optional: clear it if you want to detect "no data", but keeping the last known value is usually better for OSD
      }
    }, 100); // Update UI every 100ms (10fps) instead of network speed
    return () => clearInterval(interval);
  }, [enableTelemetry]);

  // Handle config send Packets

  const handleSend = () => {
    if (connection) {
      send(makeConfig_Packets(config));
    }
  };

  // Use a ref to hold the latest input state so we don't restart the interval on every change
  const uiStateRef = useRef(uiState);
  useEffect(() => {
    uiStateRef.current = uiState;
  }, [uiState]);

  useEffect(() => {
    if (!connection || !isRCOn) return;

    // Send RC packets at a fixed rate (e.g., 20Hz = 50ms)
    // This prevents flooding the network when inputs change rapidly
    const interval = setInterval(() => {
      send(makeRC_Packet(uiStateRef.current));
    }, 50);

    return () => clearInterval(interval);
  }, [connection, isRCOn]); // uiState is NOT a dependency here

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans p-4 lg:p-8 selection:bg-indigo-500/30">

      {/* --- HEADER --- */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            <span className={`w-3 h-8 rounded-sm inline-block ${isVehicleOffline ? "bg-red-500 animate-pulse" : "bg-indigo-500"}`} />
            PERCEPTRON
            <span className="px-2 py-0.5 rounded text-xs font-medium bg-slate-800 text-indigo-300 border border-slate-700">v2.1</span>
          </h1>
          <p className="text-slate-400 text-sm mt-1 ml-6">Remote Teleoperation Interface</p>
        </div>
        <div>
          {/* Telemetry moved to HUD */}
          <MotorTelemetry data={motorTelemetry} />
        </div>
        <div className="flex gap-4 items-center bg-slate-900/50 p-2 rounded-2xl border border-slate-800">
          {/* RC Toggle */}
          <button
            onClick={() => setIsRCOn(!isRCOn)}
            className={`p-2 rounded-full transition-colors border ${isRCOn ? "bg-indigo-500/20 text-indigo-400 border-indigo-500/30" : "bg-red-500 text-red-500 border-transparent hover:text-red-300"}`}
            title={isRCOn ? "RC Control: ON" : "RC Control: PAUSED"}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              {isRCOn ? <path d="M18.36 6.64a9 9 0 1 1-12.73 0" /> : <circle cx="12" cy="12" r="10" />}
              <line x1="12" y1="2" x2="12" y2="12" />
            </svg>
          </button>
          <ModeBadge mode={mode} />
          <StatusBadge
            active={connection}
            label={connection ? "WS CONNECTED" : "WS DISCONNECTED"}
          />

          <StatusBadge
            active={!isVehicleOffline && health?.container_status === "RUNNING"}
            label={
              !isVehicleOffline && health?.container_status === "RUNNING"
                ? "VEHICLE CONNECTED"
                : "VEHICLE OFFLINE"
            }
          />
          <div className="h-6 w-[1px] bg-slate-700" />
          <div className="flex flex-col items-end px-2">
            <span className="text-[10px] uppercase text-slate-500 font-bold">Latency</span>
            <span className={`text-sm font-mono font-bold ${isVehicleOffline ? "text-red-500" : health?.latency > 200 ? "text-amber-400" : "text-emerald-400"}`}>
              {isVehicleOffline ? "---" : health?.latency + "ms"}
            </span>
          </div>
          <button
            onClick={() => setIsTerminalMode(!isTerminalMode)}
            className={`p-2 rounded-full transition-colors ${isTerminalMode ? "bg-emerald-500/20 text-emerald-400" : "hover:bg-slate-700 text-slate-400 hover:text-white"}`}
            title="Toggle Web Terminal"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg>
          </button>
          <button
            onClick={reconnect}
            className="p-2 hover:bg-slate-700 rounded-full text-slate-400 hover:text-white transition-colors"
            title="Reconnect WebSocket"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" /><path d="M3 3v5h5" /><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" /><path d="M16 16h5v5" /></svg>
          </button>
        </div>
      </header>

      {/* --- MAIN GRID --- */}
      <main className="grid grid-cols-1 lg:grid-cols-12 gap-6 pb-20">

        {/* LEFT COLUMN: CONTROLS */}
        <div className="lg:col-span-3 space-y-6">
          <Card title="Input Visualizer">
            <div className="py-4 px-8">
              <JoystickVisualizer x={uiState.roll} y={uiState.throttle} />
            </div>
            <div className="mt-6 space-y-4">
              <ProgressBar label="Throttle (Pitch)" value={uiState.throttle} color="bg-blue-500" />
              <ProgressBar label="Steering (Roll)" value={uiState.roll} color="bg-indigo-500" />
            </div>
          </Card>

          <Card title="Speed Limiter">
            <div className="flex items-center gap-4">
              <input
                type="range" min="0" max="500" value={speed} onChange={handleChange}
                className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-500 hover:accent-indigo-400"
              />
              <span className="font-mono text-xl font-bold min-w-[3ch] text-right">{speed}</span>
            </div>
            <div className="mt-2 text-xs text-slate-500 text-center uppercase tracking-wider">RPM Limit Cap</div>
          </Card>

          {!isTerminalMode && (
            <CommandUplink
              connection={connection}
              isVehicleOffline={isVehicleOffline}
              send={send}
              onLog={addLog}
            />
          )}
          <ConfigDashboard handleSend={handleSend} config={config} setConfig={setConfig} />
        </div>




        {/* CENTER COLUMN: FEED */}
        <div className="lg:col-span-7">
          <Card className={`h-full min-h-[400px] relative group shadow-[0_0_40px_-10px_rgba(99,102,241,0.1)] ${isVehicleOffline ? "border-red-500/50" : "border-indigo-500/20"}`}>
            {/* Header Overlay */}
            <div className="absolute top-0 left-0 right-0 p-4 z-10 flex justify-between items-start bg-gradient-to-b from-black/80 to-transparent pointer-events-none">
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full animate-pulse ${isVehicleOffline ? "bg-red-500" : "bg-emerald-500"}`} />
                <span className="text-xs font-bold text-white tracking-widest drop-shadow-md">
                  {isVehicleOffline ? "SIGNAL LOST" : "LIVE FEED"}
                </span>
              </div>
            </div>

            {/* Video Container */}
            <div className="aspect-video w-full relative">

              {(!isVehicleOffline || !connection) && <CameraView key={videoKey} />}

              {/* OFFLINE OVERLAY */}
              {isVehicleOffline && (
                <div className="absolute inset-0 bg-slate-900/80 backdrop-blur-sm z-30 flex flex-col items-center justify-center text-center p-6">
                  <div className="w-16 h-16 rounded-full bg-red-500/10 border-2 border-red-500 flex items-center justify-center mb-4 animate-pulse">
                    <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" /></svg>
                  </div>
                  <h2 className="text-2xl font-bold text-white tracking-wider mb-2">VEHICLE OFFLINE</h2>
                  <p className="text-slate-400 text-sm max-w-xs">Connection to the vehicle telemetry system has been interrupted. Last signal received {lastBeat}s ago.</p>
                </div>
              )}

              {/* Crosshair Overlay (Only show if online) */}
              {!isVehicleOffline && (
                <div className="absolute inset-0 pointer-events-none opacity-30">
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-12 h-12 border border-white/50 rounded-full" />
                  <div className="absolute top-1/2 left-0 right-0 h-[1px] bg-white/20" />
                  <div className="absolute left-1/2 top-0 bottom-0 w-[1px] bg-white/20" />
                </div>
              )}
              {/* Motor Telemetry HUD */}
              {!isVehicleOffline}
            </div>

            {/* Action Overlay */}
            <button
              onClick={() => setVideoKey(k => k + 1)}
              className="absolute top-4 right-4 z-20 p-2 bg-black/40 backdrop-blur-md border border-white/10 rounded-lg hover:bg-indigo-600 hover:border-indigo-500 text-white transition-all duration-200 group-hover:opacity-100 opacity-50"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" /><path d="M3 3v5h5" /><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" /><path d="M16 16h5v5" /></svg>
            </button>
          </Card>
        </div>

        {/* RIGHT COLUMN: DIAGNOSTICS */}
        <div className="lg:col-span-2 space-y-6">
          <Card title="System Health">
            <MetricRow label="Status" value={isVehicleOffline ? "OFFLINE" : health?.container_status || "N/A"} />
            <MetricRow label="up_time" value={health?.up_time || 0} unit="s" />
            <MetricRow label="Last Beat" value={lastBeat} unit="s ago" />
          </Card>

          <Card title="Performance Controls">
            <div className="flex flex-col gap-3">
              <label className="flex items-center gap-3 cursor-pointer group">
                <div className={`w-5 h-5 rounded border flex items-center justify-center transition-colors ${enableTelemetry ? "bg-emerald-500 border-emerald-500" : "border-slate-600 bg-slate-800"}`}>
                  {enableTelemetry && <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
                </div>
                <input type="checkbox" className="hidden" checked={enableTelemetry} onChange={e => setEnableTelemetry(e.target.checked)} />
                <span className={`text-sm font-medium transition-colors ${enableTelemetry ? "text-white" : "text-slate-500"}`}>Enable Telemetry Parsing</span>
              </label>

              <label className="flex items-center gap-3 cursor-pointer group">
                <div className={`w-5 h-5 rounded border flex items-center justify-center transition-colors ${enableGraphs ? "bg-indigo-500 border-indigo-500" : "border-slate-600 bg-slate-800"}`}>
                  {enableGraphs && <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
                </div>
                <input type="checkbox" className="hidden" checked={enableGraphs} onChange={e => setEnableGraphs(e.target.checked)} />
                <span className={`text-sm font-medium transition-colors ${enableGraphs ? "text-white" : "text-slate-500"}`}>Enable Graphs</span>
              </label>
            </div>
          </Card>

          <Card title="Latency History">
            <LatencyGraph currentLatency={isVehicleOffline ? 0 : health?.latency || 0} />
          </Card>

          {enableGraphs && <TelemetryGraphs data={motorTelemetry} />}

          <Card title="Auxiliary">
            <ProgressBar label="Aux 1" value={uiState.aux1} color="bg-emerald-500" />
            <ProgressBar label="Aux 2" value={uiState.aux2} color="bg-emerald-500" />
          </Card>

          {(health?.latency > 200 || isVehicleOffline) && (
            <div className={`border rounded-xl p-4 flex items-start gap-3 ${isVehicleOffline ? "bg-red-500/10 border-red-500/20" : "bg-amber-500/10 border-amber-500/20"}`}>
              <svg className={`w-5 h-5 shrink-0 ${isVehicleOffline ? "text-red-500" : "text-amber-500"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
              <div>
                <h4 className={`font-bold text-sm ${isVehicleOffline ? "text-red-400" : "text-amber-400"}`}>
                  {isVehicleOffline ? "CRITICAL ERROR" : "High Latency"}
                </h4>
                <p className={`text-xs mt-1 ${isVehicleOffline ? "text-red-500/80" : "text-amber-500/80"}`}>
                  {isVehicleOffline ? "Vehicle telemetry lost. Check connection." : "Network conditions may affect control."}
                </p>
              </div>
            </div>
          )}

          {/* {!isTerminalMode && (
            <OutputLog logs={logs} />
          )}

          {isTerminalMode && (
            <WebTerminal
              connection={connection}
              send={send}
              logs={logs}
              isRCOn={isRCOn}
              onLog={addLog}
            />
          )} */}
        </div>
      </main>
      {/* <h3>Dynamic Telemetry Graph</h3> */}
      {/* <DynamicJsonGraph logs={logs} maxPoints={60} /> */}
    </div>
  );
}
