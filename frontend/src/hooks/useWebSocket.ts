import { useState, useEffect, useRef } from "react";

// Define the shape of our data based on the Python backend
export interface Point {
    x: number;
    y: number;
    label: number;
}

export interface Metrics {
    loss: number;
    accuracy: number;
}

export function useWebSocket(url: string) {
    // State to hold the history of points and the latest metrics
    const [points, setPoints] = useState<Point[]>([]);
    const [metrics, setMetrics] = useState<Metrics>({ loss: 1.0, accuracy: 0.0 });
    const [boundary, setBoundary] = useState<number[][]>([]); 
    
    // A ref to hold the actual connection so it doesn't reconnect on every render
    const ws = useRef<WebSocket | null>(null);
    // NEW: Fetch historical data when the hook first mounts
    // Fetch historical data when the hook first mounts
    useEffect(() => {
        fetch("http://127.0.0.1:8000/history")
        .then((res) => res.json())
        .then((data) => {
            if (data.points) setPoints(data.points);
            if (data.boundary) setBoundary(data.boundary); // Grab the background on load!
        })
        .catch((err) => console.error("Failed to fetch history:", err));
    }, []);

    useEffect(() => {
        // 1. Open the connection to FastAPI
        ws.current = new WebSocket(url);

        // 2. Listen for messages from the Python ConnectionManager
        ws.current.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === "update") {
                // Add the new point to our array
                setPoints((prev) => [...prev, data.point]);
                // Update the AI's current scorecard
                setMetrics(data.metrics);
            }
        };
    
    // 2. Listen for messages from the Python ConnectionManager
    ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === "update") {
            setPoints((prev) => [...prev, data.point]);
            setMetrics(data.metrics);
            if (data.boundary) setBoundary(data.boundary);
        } else if (data.type === "reset") {
            // NEW: When someone clicks reset, clear our local state instantly!
            setPoints([]);
            setMetrics({ loss: 1.0, accuracy: 0.0 });
        }
    };

        // 3. Clean up the connection if the user closes the page
        return () => {
            ws.current?.close();
        };
    }, [url]);

    return { points, metrics, boundary };
}
