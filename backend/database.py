from motor.motor_asyncio import AsyncIOMotorClient
import datetime
from bson.binary import Binary
import io

import os
from dotenv import load_dotenv
load_dotenv()

MONGO_DETAILS = os.getenv("MONGO_DETAILS")

# Initialize the client
client = AsyncIOMotorClient(MONGO_DETAILS)
database = client.live_neural_landscape
clicks_collection = database.get_collection("clicks")
checkpoints_collection = database.get_collection("model_checkpoints")

async def save_click_event(x: float, y: float, label: float, loss: float, accuracy: float):
    """
    Saves a single training event to MongoDB.
    """
    document = {
        "x": x,
        "y": y,
        "label": label,
        "resulting_loss": loss,
        "resulting_accuracy": accuracy,
        "timestamp": datetime.datetime.utcnow()
    }
    
    # The 'await' here is magic. It tells the server: "Go ahead and send this 
    # to the database, but don't freeze the app while waiting for it to finish saving."
    result = await clicks_collection.insert_one(document)
    return str(result.inserted_id)


async def get_all_clicks():
    """Fetches the historical clicks from the database."""
    # We grab the x, y, and label, ignoring the internal MongoDB _id
    # We'll limit it to 1000 so we don't crash the browser after days of clicking
    cursor = clicks_collection.find({}, {"_id": 0, "x": 1, "y": 1, "label": 1}).limit(1000)
    return await cursor.to_list(length=1000)


async def clear_all_clicks():
    """Deletes all training data from MongoDB."""
    await clicks_collection.delete_many({})

async def save_pytorch_checkpoint(model_bytes: bytes, total_points: int):
    """Saves a binary snapshot of the PyTorch weights."""
    document = {
        "weights": Binary(model_bytes),
        "total_points": total_points,
        "timestamp": datetime.datetime.utcnow()
    }
    await checkpoints_collection.insert_one(document)
    print(f"💾 Snapshot saved! Model memory size: {total_points} points.")

async def get_latest_checkpoint():
    """Fetches the most recent model weights from MongoDB."""
    # Sort by timestamp descending (-1) and grab the first one
    cursor = checkpoints_collection.find().sort("timestamp", -1).limit(1)
    checkpoints = await cursor.to_list(length=1)
    
    if checkpoints:
        return checkpoints[0]["weights"]
    return None