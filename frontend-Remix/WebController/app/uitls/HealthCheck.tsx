// hooks/useHealth.ts  (or .tsx if you prefer)
import { useState, useEffect } from "react";

export interface HealthData {
    connected?: string;
    latency?: number;
    container_status?: string;
    last_message_time?: number;
    up_time?: number;
}

export function useHealth() {
    const [health, setHealth] = useState<HealthData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchHealth() {
            try {
                const response = await fetch(`http://yadiec2.freedynamicdns.net:8080/health`);

                if (!response.ok) {
                    throw new Error(`Status: ${response.status}`);
                }

                const data: HealthData = await response.json();
                setHealth(data);
                setError(null);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Connection failed");
                setHealth(null);
            } finally {
                setLoading(false);
            }
        }

        // Initial fetch
        fetchHealth();

        // Poll every 1 second
        const interval = setInterval(fetchHealth, 1000);

        // Cleanup
        return () => clearInterval(interval);
    }, []);

    return { health, loading, error };
}
