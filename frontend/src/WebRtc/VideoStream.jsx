import React, { useRef, useState, useEffect } from "react";

const VideoStream = ({ ip }) => {
  const videoRef = useRef(null);
  const pcRef = useRef(null);
  const wsRef = useRef(null);
  const [streaming, setStreaming] = useState(false);
  const [status, setStatus] = useState("Disconnected");
  const [bitrate, setBitrate] = useState(0);
  const [errorMessage, setErrorMessage] = useState(null);

  const startVideo = async () => {
    if (streaming) return;

    setStatus("Connecting...");
    setErrorMessage(null);

    const pc = new RTCPeerConnection({
      iceServers: [
        { urls: "stun:stun.l.google.com:19302" }, // Add STUN for public IP discovery
        { 
          urls: "turn:13.201.65.188:3478?transport=udp",
          username: "perceptron",
          credential: "root"
        },
        { 
          urls: "turn:13.201.65.188:3478?transport=tcp", // TCP fallback for restrictive networks
          username: "perceptron",
          credential: "root"
        }
      ]
    });

    pc.ontrack = (event) => {
      if (videoRef.current) {
        videoRef.current.srcObject = event.streams[0];
      }
    };

    pc.onconnectionstatechange = () => {
      setStatus(pc.connectionState);
      if (pc.connectionState === "disconnected" || pc.connectionState === "failed") {
        setBitrate(0);
        setErrorMessage("Connection lost. Attempting to reconnect...");
        stopVideo();
        setTimeout(startVideo, 3000); // Auto-reconnect after 3s
      }
    };

    pc.oniceconnectionstatechange = () => {
      if (pc.iceConnectionState === "failed") {
        setErrorMessage("ICE connection failed. Check network or server.");
      }
    };

    pc.onicecandidate = (event) => {
      if (event.candidate && wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          candidate: {
            candidate: event.candidate.candidate,
            sdpMid: event.candidate.sdpMid,
            sdpMLineIndex: event.candidate.sdpMLineIndex
          }
        }));
      }
    };

    let statsInterval;
    const monitorStats = async () => {
      let lastBytesReceived = 0;
      let lastTimestamp = 0;
      
      statsInterval = setInterval(async () => {
        if (pc.connectionState !== "connected") {
          clearInterval(statsInterval);
          return;
        }

        try {
          const stats = await pc.getStats();
          stats.forEach(report => {
            if (report.type === "inbound-rtp" && report.kind === "video") {
              const bytesReceived = report.bytesReceived || 0;
              const timestamp = report.timestamp;
              
              if (lastBytesReceived > 0 && lastTimestamp > 0 && timestamp > lastTimestamp) {
                const deltaBytes = bytesReceived - lastBytesReceived;
                const deltaTime = (timestamp - lastTimestamp) / 1000;
                if (deltaTime > 0.001) {
                  const bitrateKbps = (deltaBytes * 8) / deltaTime / 1000;
                  setBitrate(Math.round(bitrateKbps));
                }
              }
              
              lastBytesReceived = bytesReceived;
              lastTimestamp = timestamp;
            }
          });
        } catch (err) {
          // Silent
        }
      }, 2000);
    };

    const ws = new WebSocket(`ws://${ip}/ws`);

    ws.onopen = () => {
      ws.send(JSON.stringify({ role: "browser" }));
      ws.send(JSON.stringify({ action: "request-offer" }));
    };

    ws.onmessage = async (msg) => {
      if (typeof msg.data !== 'string') return;

      try {
        const data = JSON.parse(msg.data);

        if (data.sdp && data.type) {
          if (data.type === "offer") {
            await pc.setRemoteDescription(data);
            const answer = await pc.createAnswer();
            await pc.setLocalDescription(answer);
            ws.send(JSON.stringify({
              sdp: answer.sdp,
              type: answer.type
            }));
          } else if (data.type === "answer") {
            await pc.setRemoteDescription(data);
          }
        } else if (data.candidate) {
          await pc.addIceCandidate(data.candidate);
        }
      } catch (err) {
        setErrorMessage("Signaling error. Please try again.");
      }
    };

    ws.onerror = () => {
      setErrorMessage("WebSocket connection failed.");
    };

    ws.onclose = () => {
      setStatus("Disconnected");
      setBitrate(0);
    };

    pcRef.current = pc;
    wsRef.current = ws;
    setStreaming(true);

    setTimeout(() => {
      if (pc.connectionState === "connected") {
        monitorStats();
      }
    }, 3000);
  };

  const stopVideo = () => {
    if (!streaming) return;

    if (pcRef.current) {
      pcRef.current.close();
      pcRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setStreaming(false);
    setStatus("Disconnected");
    setBitrate(0);
    setErrorMessage(null);
  };

  useEffect(() => {
    return () => {
      stopVideo();
    };
  }, []);

  return (
    <div style={{ textAlign: "center", padding: "20px" }}>
      <h2>Raspberry Pi Video Stream</h2>
      <div style={{ marginBottom: "10px", color: status === "connected" ? "green" : "orange" }}>
        Status: {status}
      </div>
      {errorMessage && (
        <div style={{ marginBottom: "10px", color: "red" }}>
          {errorMessage}
        </div>
      )}
      <div style={{ marginBottom: "10px" }}>
        Bitrate: {bitrate} kbps ({(bitrate / 1000).toFixed(2)} Mbps)
      </div>
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        style={{ 
          width: "640px", 
          height: "480px", 
          borderRadius: "10px", 
          background: "black",
          border: "2px solid #ccc",
          display: status === "connected" ? "block" : "none",
          objectFit: "contain"
        }}
        onError={() => setErrorMessage("Video playback error. Check stream.")}
      />
      {status !== "connected" && (
        <div style={{ 
          width: "640px", 
          height: "480px", 
          borderRadius: "10px", 
          background: "#333",
          border: "2px solid #ccc",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "white",
          margin: "0 auto"
        }}>
          {status === "connecting" ? "Connecting..." : status}
        </div>
      )}
      <div style={{ marginTop: "1rem" }}>
        <button 
          onClick={startVideo} 
          disabled={streaming}
          style={{ margin: "0 10px", padding: "10px 20px" }}
        >
          Start Video
        </button>
        <button 
          onClick={stopVideo} 
          disabled={!streaming}
          style={{ margin: "0 10px", padding: "10px 20px" }}
        >
          Stop Video
        </button>
      </div>
    </div>
  );
};

export default VideoStream;