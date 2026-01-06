import { useEffect, useRef, useState } from 'react';

interface UseWebSocketReturn {
    send: (data: string | ArrayBuffer | Blob) => void;
    status: 'connecting' | 'open' | 'closing' | 'closed' | 'disconnected';
    connection: boolean;
    lastMessage: any; // Added to store the received data
    reconnect: () => void;
}

export const useWebSocket = (url: string | null | undefined): UseWebSocketReturn => {
    const socket = useRef<WebSocket | null>(null);
    const [connection, setConnection] = useState<boolean>(false);
    const [lastMessage, setLastMessage] = useState<any>(null); // State for incoming messages
    const [isConnected, setIsConnected] = useState(false);
    const [reconnectTrigger, setReconnectTrigger] = useState(0);

    const reconnect = () => {
        setReconnectTrigger(prev => prev + 1);
    };

    const status = socket.current
        ? (
            socket.current.readyState === WebSocket.CONNECTING ? 'connecting' :
                socket.current.readyState === WebSocket.OPEN ? 'open' :
                    socket.current.readyState === WebSocket.CLOSING ? 'closing' :
                        'closed'
        )
        : 'disconnected';

    useEffect(() => {
        if (!url) {
            setConnection(false);
            return;
        }

        const ws = new WebSocket(url);
        ws.binaryType = "arraybuffer";
        socket.current = ws;

        ws.onopen = () => {
            console.log('WebSocket connected');
            setConnection(true);
        };

        // --- RECEIVER LOGIC START ---
        ws.onmessage = (event: MessageEvent) => {
            // You can parse JSON here if your server sends JSON
            try {
                const data = JSON.parse(event.data);
                setLastMessage(data);
            } catch (e) {
                setLastMessage(event.data);
            }
        };
        // --- RECEIVER LOGIC END ---

        ws.onclose = () => {
            console.log('WebSocket closed');
            setConnection(false);
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            setConnection(false);
        };

        return () => {
            if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
                ws.close();
            }
        };
    }, [url, reconnectTrigger]);


    const send = (data: string | ArrayBuffer | Blob) => {
        // console.log("Internal Send Triggered. Current state:", socket.current?.readyState);

        if (socket.current && socket.current.readyState === WebSocket.OPEN) {
            socket.current.send(data);
            // console.log("Data successfully sent to browser buffer");
        } else {
            console.warn('Cannot send: WebSocket is NOT open. State is:', socket.current?.readyState);
        }
    };

    return { send, status, connection, lastMessage, reconnect };
};
