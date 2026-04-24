# The Live Neural Landscape 🧠⚡

An interactive, real-time multiplayer Machine Learning playground. 

This project bridges the gap between Data Science and Full-Stack Engineering. Instead of static datasets and batch-trained models, the Live Neural Landscape uses **Online Learning** to train AI models incrementally in real-time, instantly broadcasting the updated decision boundaries to all connected users via WebSockets.

![Tech Stack](https://img.shields.io/badge/Stack-Next.js%20%7C%20FastAPI%20%7C%20PyTorch%20%7C%20MongoDB-blue)

## 💡 How to Explain This Project (The Elevator Pitch)

If you are looking at this for my portfolio, here is what makes this architecture stand out:

* **Real-Time Online Learning:** The AI doesn't train on historical CSV files. It trains dynamically in-memory on single user clicks, adjusting its math and redrawing its decision boundaries in milliseconds.
* **The Algorithm Arena:** Users can seamlessly hot-swap the active AI brain from a deep PyTorch Neural Network to Scikit-Learn models (Decision Trees, SVM, KNN) on the fly to visually compare how different algorithms partition the exact same data space.
* **Stateful Multiplayer Synchronization:** Built with a custom FastAPI WebSocket manager, the canvas allows multiple users to collaborate simultaneously. Every click, model update, and board reset is synced across all clients with zero lag.
* **MLOps & Persistence:** The system features an automated checkpointing pipeline. Every 50 training events, the PyTorch model serializes its `state_dict` into binary format and saves it to MongoDB. If the server crashes, it automatically fetches and rehydrates the latest brain on reboot.

## ✨ Core Features
- **Interactive HTML5 Canvas:** Draw multi-class data points (Red, Green, Blue, Yellow).
- **Live Decision Boundaries:** Watch the background physically warp as the AI calculates spatial territories.
- **Real-Time Telemetry:** Recharts dashboard streaming live Loss and Accuracy metrics.
- **In-Memory History:** Late-joining clients instantly download the current board state and boundaries.

---

## 🛠️ Tech Stack
* **Frontend:** Next.js (TypeScript), Tailwind CSS, Recharts, Lucide-React
* **Backend:** FastAPI (Python), WebSockets, Asyncio
* **Machine Learning:** PyTorch, Scikit-Learn, NumPy
* **Database:** MongoDB (via Motor Asyncio Driver)

---

## 🚀 How to Run Locally

### Prerequisites
Before you begin, ensure you have the following installed:
1. **Node.js** (v18+)
2. **Python** (3.10+)
3. **MongoDB** (Running locally on default port `27017` via MongoDB Compass or Docker)

### 1. Clone the Repository
```bash
git clone [https://github.com/shreyaallupati/The-Live-Neural-Landscape.git](https://github.com/shreyaallupati/The-Live-Neural-Landscape.git)
cd live-neural-landscape
```

### 2. Start the Backend (FastAPI + AI Engine)
Open a terminal and navigate to the backend folder:
```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: .\venv\Scripts\activate

# Install the Python dependencies
pip install fastapi uvicorn torch motor websockets pydantic scikit-learn numpy

# Run the server
uvicorn main:app --reload
```
*(The server will boot up on `http://127.0.0.1:8000` and automatically check MongoDB for previous model checkpoints).*

### 3. Start the Frontend (Next.js)
Open a **second** terminal window and navigate to the frontend folder:
```bash
cd frontend

# Install Node modules
npm install

# Run the development server
npm run dev
```

### 4. Play!
Open your browser and navigate to `http://localhost:3000`. 
Open a second tab to see the multiplayer WebSockets in action!
