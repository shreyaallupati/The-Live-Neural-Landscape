from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import asyncio
from contextlib import asynccontextmanager
from model import LiveNeuralNet
from database import save_click_event, get_all_clicks, clear_all_clicks, save_pytorch_checkpoint, get_latest_checkpoint
from model import ModelArena


@asynccontextmanager
async def lifespan(app: FastAPI):
    # This runs ONCE when the server starts up
    print("🚀 Server booting up. Checking for model checkpoints...")
    latest_weights = await get_latest_checkpoint()
    
    if latest_weights:
        # We found a brain! Let's load it.
        ai_model.load_pytorch_state_bytes(latest_weights)
        print("✅ Successfully loaded previous PyTorch checkpoint from MongoDB!")
    else:
        print("🧠 No checkpoints found. Starting with a fresh PyTorch brain.")
        
    yield 
    # This runs ONCE when the server is shutting down
    print("🛑 Server is shutting down. Goodbye!")

app = FastAPI(lifespan=lifespan)


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Allows your Next.js app
    allow_credentials=True,
    allow_methods=["*"], # Allows POST, GET, etc.
    allow_headers=["*"],
)

# 1. Instantiate the AI Model in memory
ai_model = ModelArena()

# 2. WebSocket Connection Manager
# This keeps track of everyone currently looking at the Next.js canvas
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

# 3. Data Schema for User Clicks
# FastAPI uses Pydantic to strictly validate incoming data
class ClickData(BaseModel):
    x: float
    y: float
    label: float 

class SwitchData(BaseModel):
    model_name: str  # "pytorch", "tree", "svm", or "knn"


# 4. The Concurrency Lock 
# Because we have multiple users, two people might click at the exact same millisecond.
# PyTorch will crash if two threads try to update the math weights simultaneously.
# This lock forces the server to process clicks one at a time, in a rapid queue.
training_lock = asyncio.Lock()

# 5. Endpoints

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Users connect here to receive live updates."""
    await manager.connect(websocket)
    try:
        while True:
            # We keep the connection open. In this architecture, users send clicks via POST, 
            # and only *receive* data through this WebSocket.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/")
async def root():
    return {"message": "The Live Neural Landscape Backend is running!"}

@app.post("/click")
async def register_click(data: ClickData):
    """Users POST their clicks here to train the model."""
    
    # 1. Safely train the model inside the lock
    async with training_lock:
        loss, accuracy = ai_model.train_single_point(data.x, data.y, data.label)
        boundary_grid = ai_model.get_decision_boundary()

        # Every 50 points, we save the brain to MongoDB.
        current_memory_size = len(ai_model.memory)
        if current_memory_size > 0 and current_memory_size % 50 == 0:
            weight_bytes = ai_model.get_pytorch_state_bytes()
            asyncio.create_task(save_pytorch_checkpoint(weight_bytes, current_memory_size))
        
    # 2. Save the event to MongoDB
    await save_click_event(data.x, data.y, data.label, loss, accuracy)
        
    # 3. Prepare the announcement
    update_message = {
        "type": "update",
        "point": {"x": data.x, "y": data.y, "label": data.label},
        "metrics": {"loss": loss, "accuracy": accuracy},
        "boundary": boundary_grid
    }
    
    # 4. Broadcast the new point and the model's new scores to everyone
    await manager.broadcast(update_message)
    
    return {"status": "success", "loss": loss, "accuracy": accuracy}

@app.get("/history")
async def get_history():
    """Returns the historical points from the active arena memory."""
    # Convert the Arena's memory tuples (x, y, label) back into dictionaries for the frontend
    points = [{"x": m[0], "y": m[1], "label": m[2]} for m in ai_model.memory]
    
    # Also send the current boundary so the background loads instantly!
    boundary = ai_model.get_decision_boundary()
    
    return {"points": points, "boundary": boundary}

@app.post("/switch")
async def switch_model(data: SwitchData):
    """Swaps the AI brain and forces a board redraw."""
    async with training_lock:
        loss, accuracy = ai_model.set_model(data.model_name)
        boundary_grid = ai_model.get_decision_boundary()
        
    update_message = {
        "type": "update",
        # We send a dummy point just to trigger the UI update cleanly
        "point": {"x": -1, "y": -1, "label": 0}, 
        "metrics": {"loss": loss, "accuracy": accuracy},
        "boundary": boundary_grid
    }
    await manager.broadcast(update_message)
    return {"status": "switched"}

@app.post("/reset")
async def reset_board():
    """Wipes the arena memory, resets the PyTorch model, and clears all screens."""
    
    # 1. Reset the Arena memory safely
    async with training_lock:
        ai_model.reset()
        
    # 2. Broadcast a "reset" command to all connected browsers
    await manager.broadcast({"type": "reset"})
    
    return {"status": "success"}