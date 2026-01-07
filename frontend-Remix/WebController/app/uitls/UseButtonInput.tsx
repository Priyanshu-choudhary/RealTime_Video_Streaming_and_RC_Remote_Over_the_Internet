import { useRef, useState, useEffect, useCallback } from "react";

// 1. Rename to use... (Hook convention)
export default function useButtonInput() {
    const throttleRef = useRef(1500);
    const rollRef = useRef(1500);
    const aux1Ref = useRef(1000);
    const aux2Ref = useRef(1000);
    const speedRef = useRef(0);

    const [uiState, setUiState] = useState({
        throttle: 1500,
        roll: 1500,
        aux1: 1000,
        aux2: 1000,
    });

    const [speed, setSpeed] = useState(0);

    // Auto Mode Ref
    const isAutoModeRef = useRef(false);

    // Calculate Mode
    const getMode = () => {
        if (isAutoModeRef.current) return "AUTO";
        if (aux2Ref.current > 1500) return "SEMI-AUTO"; // 'f' key active
        return "MANUAL";
    };

    const [mode, setMode] = useState("MANUAL");

    // 2. Wrap in useCallback or update logic to avoid stale closures
    const updateUiState = useCallback(() => {
        setUiState({
            throttle: throttleRef.current,
            roll: rollRef.current,
            aux1: aux1Ref.current,
            aux2: aux2Ref.current,
        });
        setMode(getMode());
    }, []);

    const handleKeyDown = useCallback((e: KeyboardEvent) => {
        // Prevent default browser search behavior for 'f' if needed, but 'a' is safe usually.
        // If the user is typing in an input field, this might trigger. 
        // We assume global control flavor.

        switch (e.key) {
            case 'a':
                isAutoModeRef.current = !isAutoModeRef.current;
                if (isAutoModeRef.current) {
                    throttleRef.current = 1500 - speedRef.current;
                    aux2Ref.current = 2000;
                } else {
                    throttleRef.current = 1500;
                    aux2Ref.current = 1000;
                }
                break;
            case 'ArrowDown':
                if (!isAutoModeRef.current) throttleRef.current = 1500 + speedRef.current;
                break;
            case 'ArrowUp':
                if (!isAutoModeRef.current) throttleRef.current = 1500 - speedRef.current;
                break;
            case 'ArrowRight':
                rollRef.current = 1500 - speedRef.current;
                break;
            case 'ArrowLeft':
                rollRef.current = 1500 + speedRef.current;
                break;
            case ' ':
                aux1Ref.current = 2000;
                break;
            case 'f':
                aux2Ref.current = aux2Ref.current === 1000 ? 2000 : 1000;
                break;
            default:
                return;
        }
        updateUiState();
    }, [updateUiState]);

    const handleKeyUp = useCallback((e: KeyboardEvent) => {
        if (['ArrowUp', 'ArrowDown'].includes(e.key)) {
            if (!isAutoModeRef.current) throttleRef.current = 1500;
        }
        if (['ArrowLeft', 'ArrowRight'].includes(e.key)) {
            rollRef.current = 1500;
        }
        if (e.key === ' ') {
            aux1Ref.current = 1000;
        }
        updateUiState();
    }, [updateUiState]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newSpeed = Number(e.target.value);
        setSpeed(newSpeed);
        speedRef.current = newSpeed;

        if (isAutoModeRef.current) {
            throttleRef.current = 1500 + newSpeed;
            updateUiState();
        }
    };

    useEffect(() => {
        window.addEventListener('keydown', handleKeyDown);
        window.addEventListener('keyup', handleKeyUp);

        return () => {
            window.removeEventListener('keydown', handleKeyDown);
            window.removeEventListener('keyup', handleKeyUp);
        };
    }, [handleKeyDown, handleKeyUp]); // 3. Add dependencies here

    // 4. Return the data so your component can use it
    return { uiState, speed, handleChange, mode };
};
