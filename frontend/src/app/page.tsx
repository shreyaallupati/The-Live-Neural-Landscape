"use client";

import { useEffect, useRef, useState } from "react";
import { useWebSocket } from "../hooks/useWebSocket";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Brain, Target, Activity } from "lucide-react";

export default function LiveNeuralLandscape() {
  // Connect to our FastAPI WebSocket
  const { points, metrics, boundary } = useWebSocket("ws://127.0.0.1:8000/ws");
  
  // 0=Red, 1=Green, 2=Blue, 3=Yellow
  const [activeColor, setActiveColor] = useState<0 | 1 | 2 | 3>(0); 
  const [activeBrain, setActiveBrain] = useState<string>("pytorch");
  // References for drawing
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  // State for the UI
  const [chartData, setChartData] = useState<{ step: number; loss: number }[]>([]);

  // Keep a history of the loss for the Recharts graph
  useEffect(() => {
    if (points.length === 0) {
      setChartData([]); // Clear the graph if the board is wiped
    } else if (metrics.loss !== 1.0) {
      setChartData((prev) => [
        ...prev,
        { step: prev.length + 1, loss: metrics.loss },
      ]);
    }
  }, [metrics, points.length]);

  // Draw the boundary and dots
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return; // FIXED: Only check canvas here
    
    const ctx = canvas.getContext("2d");
    if (!ctx) return; // FIXED: Check ctx after defining it

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Color palette for Backgrounds (Light) vs Points (Dark)
    const bgColors = ["#fee2e2", "#dcfce7", "#dbeafe", "#fef9c3"]; // Light Red, Green, Blue, Yellow
    const ptColors = ["#ef4444", "#22c55e", "#3b82f6", "#eab308"]; // Solid Red, Green, Blue, Yellow

    // 1. Draw the Decision Boundary Background
    if (boundary && boundary.length > 0) {
      const gridSize = boundary.length;
      const cellWidth = canvas.width / gridSize;
      const cellHeight = canvas.height / gridSize;

      for (let i = 0; i < gridSize; i++) {
        for (let j = 0; j < gridSize; j++) {
          ctx.fillStyle = bgColors[boundary[i][j]];
          // X and Y are flipped in array indexing [row][col] -> [y][x]
          ctx.fillRect(j * cellWidth, i * cellHeight, cellWidth + 1, cellHeight + 1); 
        }
      }
    }

    // 2. Draw the Dots on top
    points.forEach((p) => {
      ctx.beginPath();
      ctx.arc(p.x * canvas.width, p.y * canvas.height, 6, 0, 2 * Math.PI);
      ctx.fillStyle = ptColors[p.label];
      ctx.fill();
      ctx.strokeStyle = "#0f172a";
      ctx.stroke();
      ctx.closePath();
    });
  }, [points, boundary]);

  // Handle user clicks to train the model
  const handleCanvasClick = async (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Get the exact pixel the user clicked
    const rect = canvas.getBoundingClientRect();
    const xPixel = e.clientX - rect.left;
    const yPixel = e.clientY - rect.top;

    // Normalize coordinates to be between 0.0 and 1.0 for PyTorch
    const xNormalized = xPixel / canvas.width;
    const yNormalized = yPixel / canvas.height;

    // Send the POST request to the FastAPI server
    try {
      await fetch("http://127.0.0.1:8000/click", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          x: xNormalized,
          y: yNormalized,
          label: activeColor, // FIXED: Now dynamically sends 0, 1, 2, or 3
        }),
      });
    } catch (error) {
      console.error("Failed to send training data:", error);
    }
  };

  const handleResetClick = async () => {
    try {
      await fetch("http://127.0.0.1:8000/reset", { method: "POST" });
    } catch (error) {
      console.error("Failed to trigger reset:", error);
    }
  };

  const handleBrainChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newBrain = e.target.value;
    setActiveBrain(newBrain);
    try {
      await fetch("http://127.0.0.1:8000/switch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model_name: newBrain }),
      });
    } catch (error) {
      console.error("Failed to switch brain:", error);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 p-8 font-sans">
      <header className="mb-8 flex items-center gap-3">
        <Brain className="w-8 h-8 text-indigo-400" />
        <h1 className="text-3xl font-bold tracking-tight">The Live Neural Landscape</h1>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* LEFT PANEL: The Canvas */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Target className="w-5 h-5 text-slate-400" /> Training Canvas
            </h2>
            
            {/* THE NEW BRAIN SELECTOR */}
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-slate-400 flex items-center gap-2">
                <Brain className="w-4 h-4" /> Active Brain:
              </span>
              <select 
                value={activeBrain}
                onChange={handleBrainChange}
                className="bg-slate-800 border border-slate-700 text-white text-sm rounded-md focus:ring-indigo-500 focus:border-indigo-500 block p-2"
              >
                <option value="pytorch">PyTorch Neural Net</option>
                <option value="tree">Decision Tree</option>
                <option value="svm">Support Vector Machine</option>
                <option value="knn">K-Nearest Neighbors</option>
              </select>
            </div>
          </div>
          
          {/* FIXED: 4 Color Buttons + Reset */}
          <div className="flex flex-wrap gap-2 mb-4">
            <button
              onClick={() => setActiveColor(0)}
              className={`px-4 py-2 rounded-md font-medium transition-colors ${
                activeColor === 0 ? "bg-red-500 text-white" : "bg-slate-800 text-slate-300 hover:bg-slate-700"
              }`}
            >
              Red (0)
            </button>
            <button
              onClick={() => setActiveColor(1)}
              className={`px-4 py-2 rounded-md font-medium transition-colors ${
                activeColor === 1 ? "bg-green-500 text-white" : "bg-slate-800 text-slate-300 hover:bg-slate-700"
              }`}
            >
              Green (1)
            </button>
            <button
              onClick={() => setActiveColor(2)}
              className={`px-4 py-2 rounded-md font-medium transition-colors ${
                activeColor === 2 ? "bg-blue-500 text-white" : "bg-slate-800 text-slate-300 hover:bg-slate-700"
              }`}
            >
              Blue (2)
            </button>
            <button
              onClick={() => setActiveColor(3)}
              className={`px-4 py-2 rounded-md font-medium transition-colors ${
                activeColor === 3 ? "bg-yellow-500 text-white" : "bg-slate-800 text-slate-300 hover:bg-slate-700"
              }`}
            >
              Yellow (3)
            </button>
            
            <div className="flex-1"></div> {/* Spacer */}
            
            <button
              onClick={handleResetClick}
              className="px-4 py-2 rounded-md font-medium transition-colors bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white border border-slate-700"
            >
              Clear Board
            </button>
          </div>
          
          <div className="relative flex justify-center bg-slate-950 rounded-lg border border-slate-700 overflow-hidden cursor-crosshair">
            <canvas
              ref={canvasRef}
              width={500}
              height={500}
              onClick={handleCanvasClick}
              className="block"
            />
          </div>
          <p className="text-slate-400 text-sm mt-4 text-center">
            Click anywhere on the canvas to place a point and instantly train the model.
          </p>
        </div>

        {/* RIGHT PANEL: Live Telemetry */}
        <div className="flex flex-col gap-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
              <div className="text-slate-400 text-sm font-medium mb-1">Live Loss</div>
              <div className="text-4xl font-bold text-indigo-400">
                {metrics.loss.toFixed(4)}
              </div>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
              <div className="text-slate-400 text-sm font-medium mb-1">Latest Prediction</div>
              <div className="text-4xl font-bold text-emerald-400">
                {metrics.accuracy === 1 ? "Correct" : "Wrong"}
              </div>
            </div>
          </div>

          {/* Recharts Graph */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl flex-1 min-h-[300px]">
            <h2 className="text-xl font-semibold flex items-center gap-2 mb-6">
              <Activity className="w-5 h-5 text-slate-400" /> Training Loss Curve
            </h2>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="step" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" domain={['auto', 'auto']} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc' }}
                  itemStyle={{ color: '#818cf8' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="loss" 
                  stroke="#818cf8" 
                  strokeWidth={3} 
                  dot={false}
                  isAnimationActive={false} // Disabled animation so it updates instantly
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}