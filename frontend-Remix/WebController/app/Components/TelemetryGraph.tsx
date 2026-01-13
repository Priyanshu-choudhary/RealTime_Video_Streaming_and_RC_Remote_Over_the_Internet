import React, { useMemo, useState, useEffect } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

export type LogEntry = {
  time: string;        // e.g. "14:40:03"
  msg: string;         // JSON string, e.g. '{"error":5.9,"correction":-6.1}'
  source: "TX" | "RX";
};

interface DynamicJsonGraphProps {
  logs: LogEntry[];        // incoming log array (most recent at end)
  maxPoints?: number;      // how many points to keep in history (default 50)
  defaultVisible?: string[]; // optional list of keys to show initially
}

/**
 * Helper: provide an array of colors for lines.
 * It will cycle if there are more keys than colors.
 */
const COLORS = [
  "#1f77b4", // blue
  "#ff7f0e", // orange
  "#2ca02c", // green
  "#d62728", // red
  "#9467bd", // purple
  "#8c564b", // brown
  "#e377c2", // pink
  "#7f7f7f", // gray
  "#bcbd22", // olive
  "#17becf", // cyan
];

const DynamicJsonGraph: React.FC<DynamicJsonGraphProps> = ({
  logs,
  maxPoints = 50,
  defaultVisible = [],
}) => {
  /**
   * 1) Parse logs -> data points with flattened numeric keys
   * We keep order and slice to maxPoints
   */
  const parsedData = useMemo(() => {
    const slice = logs.slice(-maxPoints);
    const out: Array<Record<string, any>> = [];

    for (const entry of slice) {
      let obj: any = { time: entry.time };

      try {
        const parsed = JSON.parse(entry.msg);
        if (parsed && typeof parsed === "object") {
          // copy numeric-ish fields
          for (const k of Object.keys(parsed)) {
            const v = parsed[k];
            // treat numbers or numeric strings as numbers
            const n = typeof v === "number" ? v : Number(v);
            if (Number.isFinite(n)) {
              obj[k] = n;
            } else {
              // keep non-numeric as undefined (recharts ignores)
              obj[k] = undefined;
            }
          }
        }
      } catch (e) {
        // invalid JSON -> ignore
      }

      out.push(obj);
    }
    return out;
  }, [logs, maxPoints]);

  /**
   * 2) Discover all property keys across parsedData (excluding 'time')
   */
  const availableKeys = useMemo(() => {
    const s = new Set<string>();
    for (const d of parsedData) {
      for (const k of Object.keys(d)) {
        if (k === "time") continue;
        s.add(k);
      }
    }
    return Array.from(s);
  }, [parsedData]);

  /**
   * 3) Manage selection (which keys are shown)
   * - If user provides defaultVisible we initialize with that (intersected with available).
   * - If no defaults, show all keys by default.
   * - When new keys appear, add them to selection (preserve user's previous toggles).
   */
  const [selectedKeys, setSelectedKeys] = useState<string[]>(() => {
    return defaultVisible.length ? defaultVisible.slice() : [];
  });

  useEffect(() => {
    if (availableKeys.length === 0) {
      setSelectedKeys([]); // no keys available
      return;
    }

    setSelectedKeys((prev) => {
      // If initial state was empty -> show all keys by default
      if (prev.length === 0 && defaultVisible.length === 0) {
        return availableKeys.slice();
      }
      // Merge: keep previously selected, and add any newly discovered keys
      const merged = Array.from(new Set([...prev, ...availableKeys]));
      // Keep order stable: order by availableKeys first then any extras
      const ordered = merged.filter((k) => availableKeys.includes(k))
        .concat(merged.filter((k) => !availableKeys.includes(k)));
      return ordered;
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [availableKeys.join("|")]); // only when keys change

  const toggleKey = (key: string) => {
    setSelectedKeys((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    );
  };

  const selectAll = () => setSelectedKeys(availableKeys.slice());
  const clearAll = () => setSelectedKeys([]);

  return (
    <div style={{ width: "100%" }}>
      <div style={{ display: "flex", alignItems: "center", marginBottom: 8 }}>
        <div style={{ marginRight: 12 }}>
          <button onClick={selectAll} disabled={availableKeys.length === 0}>
            Select All
          </button>{" "}
          <button onClick={clearAll} disabled={availableKeys.length === 0}>
            Clear
          </button>
        </div>

        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {availableKeys.map((k) => {
            const checked = selectedKeys.includes(k);
            const color = COLORS[availableKeys.indexOf(k) % COLORS.length];
            return (
              <label
                key={k}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 6,
                  marginRight: 8,
                  userSelect: "none",
                }}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => toggleKey(k)}
                />
                <span
                  style={{
                    width: 10,
                    height: 10,
                    background: color,
                    display: "inline-block",
                    marginRight: 6,
                    borderRadius: 2,
                  }}
                />
                <span style={{ fontSize: 13 }}>{k}</span>
              </label>
            );
          })}
        </div>
      </div>

      <div style={{ width: "100%", height: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={parsedData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" minTickGap={20} />
            <YAxis />
            <Tooltip />
            <Legend />
            {selectedKeys.map((k, idx) => (
              <Line
                key={k}
                type="monotone"
                dataKey={k}
                stroke={COLORS[idx % COLORS.length]}
                dot={false}
                isAnimationActive={false}
                strokeWidth={2}
                connectNulls={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default DynamicJsonGraph;
