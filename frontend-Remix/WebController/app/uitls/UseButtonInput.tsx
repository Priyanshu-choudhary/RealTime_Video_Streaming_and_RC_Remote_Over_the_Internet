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

    // 2. Wrap in useCallback or update logic to avoid stale closures
    const updateUiState = useCallback(() => {
        setUiState({
            throttle: throttleRef.current,
            roll: rollRef.current,
            aux1: aux1Ref.current,
            aux2: aux2Ref.current,
        });
    }, []);

    const handleKeyDown = useCallback((e) => {
        switch (e.key) {
            case 'ArrowDown':
                throttleRef.current = 1500 + speedRef.current;
                break;
            case 'ArrowUp':
                throttleRef.current = 1500 - speedRef.current;
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

    const handleKeyUp = useCallback((e) => {
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
    }, [updateUiState]);

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
    }, [handleKeyDown, handleKeyUp]); // 3. Add dependencies here

    // 4. Return the data so your component can use it
    return { uiState, speed, handleChange };
};
