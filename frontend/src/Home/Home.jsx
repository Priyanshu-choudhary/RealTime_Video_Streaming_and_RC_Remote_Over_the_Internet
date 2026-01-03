import React, { useEffect, useState, useRef } from 'react';
import { FaCar, FaBatteryFull, FaTachometerAlt } from 'react-icons/fa';
import { MdSpeed, MdPlayArrow, MdStop } from 'react-icons/md';
import './RobotController.css';
import useWebSocket from './Websocket';
import MapWithGPS from '../Map/Map';
import VideoStream from '../WebRtc/VideoStream';
import TextField from "@mui/material/TextField";


const RobotController = () => {
  const WS_ENDPOINT = import.meta.env.VITE_WS_ENDPOINT;
  const [ip, setIp] = useState(WS_ENDPOINT);
  const { send, status, connection } = useWebSocket(`wss://${ip}/ws`);
  const speedRef = useRef(0);
  const throttleRef = useRef(1500);
  const rollRef = useRef(1500);
  const aux1Ref = useRef(1000);
  const aux2Ref = useRef(1000);
  const intervalRef = useRef(null);
  const lastPacketRef = useRef(null);

  const [uiState, setUiState] = useState({
    throttle: 1500,
    roll: 1500,
    aux1: 1000,
    aux2: 1000,
  });
  const [isSending, setIsSending] = useState(false);
  const [speed, setSpeed] = useState(0);

useEffect(() => {
 console.log(uiState);
 
}, [uiState])


  const packBinaryData = () => {
    // Create a 6-byte buffer (4 values * 10 bits = 40 bits, padded to 48 bits)
    const buffer = new ArrayBuffer(6);
    const view = new DataView(buffer);

    // Pack each 10-bit value into the buffer
    // Shift values to 0–1023 range (subtract 1000, clamp to 0–1023)
    const throttle = Math.max(0, Math.min(1023, throttleRef.current - 1000));
    const roll = Math.max(0, Math.min(1023, rollRef.current - 1000));
    const aux1 = Math.max(0, Math.min(1023, aux1Ref.current - 1000));
    const aux2 = Math.max(0, Math.min(1023, aux2Ref.current - 1000));

    // Pack two 10-bit values per 3 bytes (24 bits)
    // First 3 bytes: throttle (10 bits), roll (10 bits), 4 bits padding
    view.setUint16(0, (throttle << 6) | (roll >> 4)); // Bits 0–15
    view.setUint8(2, (roll & 0x0F) << 4); // Bits 16–19 (lower 4 bits of roll)

    // Second 3 bytes: aux1 (10 bits), aux2 (10 bits), 4 bits padding
    view.setUint16(3, (aux1 << 6) | (aux2 >> 4)); // Bits 24–39
    view.setUint8(5, (aux2 & 0x0F) << 4); // Bits 40–43 (lower 4 bits of aux2)

    return buffer;
  };

  const startSendingData = () => {
    if (!intervalRef.current) {
      intervalRef.current = setInterval(() => {
        const binaryData = packBinaryData();
        send(binaryData); // Send binary data
      }, 50);
      setIsSending(true);
    }
  };

  const stopSendingData = () => {
    clearInterval(intervalRef.current);
    intervalRef.current = null;
    setIsSending(false);
  };

  const toggleSending = () => {
    if (isSending) stopSendingData();
    else startSendingData();
  };

  const handleKeyDown = (e) => {
    switch (e.key) {
      case 'ArrowUp':
        throttleRef.current = 1500 + speedRef.current;
        break;
      case 'ArrowDown':
        throttleRef.current = 1500 - speedRef.current;
        break;
      case 'ArrowLeft':
        rollRef.current = 1500 - speedRef.current;
        break;
      case 'ArrowRight':
        rollRef.current = 1500 + speedRef.current;
        break;
      case ' ':
        aux1Ref.current = 2000;
        break;
      case 'f':
        aux2Ref.current = aux2Ref.current === 1000 ? 2000 : 1000;
        break;
      default:
        break;
    }
    updateUiState();
  };

  const handleKeyUp = (e) => {
    if (['ArrowUp', 'ArrowDown'].includes(e.key)) {
      throttleRef.current = 1500;
    }
    if (['ArrowLeft', 'ArrowRight'].includes(e.key)) {
      rollRef.current = 1500;
    }
    if (e.key === ' ') {
      aux1Ref.current = 1000;
    }
    updateUiState();
  };

  const updateUiState = () => {
    setUiState({
      throttle: throttleRef.current,
      roll: rollRef.current,
      aux1: aux1Ref.current,
      aux2: aux2Ref.current,
    });
  };

  const handleChange = (e) => {
    const newSpeed = Number(e.target.value);
    setSpeed(newSpeed);
    speedRef.current = newSpeed;
  };

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, []);

  return (
    <div className="flex">
      <div className="p-5 w-1/2">
        <header className="controller-header">
          <FaCar className="header-icon" />
          <h1>Car Remote Controller</h1>
        <TextField
          label="Custom IP Address"
          variant="outlined"
          size="small"
          value={ip}
          onChange={(e) => setIp(e.target.value)}
          placeholder="192.168.1.10"
        />

        </header>

        <div className="flex justify-between">
          <div className="status-section">
            <div className="status-item">
              <FaBatteryFull className="status-icon" />
              <span>Battery Voltage: {status.batteryVoltage ? `${status.batteryVoltage} V` : 'N/A'}</span>
            </div>
            <div className="status-item">
              <MdSpeed className="status-icon" />
              <span>Connected Clients: {status.connectedClients}</span>
            </div>
            <div className="status-item">
              <span className="flex gap-5">
                Status: <span style={{ color: connection ? 'green' : 'red' }}>{connection ? 'Connected' : 'Not Connected'}</span>
              </span>
            </div>
          </div>

          <div className="controls-section">
            <div className="speed-control">
              <label>Speed:</label>
              <input
                type="range"
                min="0"
                max="500"
                value={speed}
                onChange={handleChange}
              />
              <span>{Math.round((speed / 500) * 100)}%</span>
            </div>

            <div className="action-buttons">
              <button
                className={`control-button ${isSending ? 'stop-button' : 'start-button'}`}
                onClick={toggleSending}
              >
                {isSending ? <MdStop /> : <MdPlayArrow />}
                {isSending ? 'Stop' : 'Start'}
              </button>
            </div>
          </div>
        </div>

        <div className="telemetry-section flex justify-between">
          <div className="font-bold text-left">
            <h2>Telemetry</h2>
            <div className="telemetry-data font-normal ml-4">
              <div>Throttle: {uiState.throttle}</div>
              <div>Roll: {uiState.roll}</div>
              <div>Aux1: {uiState.aux1}</div>
              <div>Aux2: {uiState.aux2}</div>
            </div>
          </div>

          <div className="font-bold text-left">
            <h2>GPS</h2>
            <div className="telemetry-data font-normal ml-4">
              <div>location: {status.lat} {status.log}</div>
              <div>speed: {status.speed} km/h</div>
              <div>satellites: {status.sat}</div>
              <div>time: {status.time}</div>
            </div>
          </div>
        </div>
      </div>
      {/* <div className="w-1/2 p-5">
        <MapWithGPS status={status} />
      </div> */}
      <VideoStream ip={ip}/>
    </div>
  );
};

export default RobotController;