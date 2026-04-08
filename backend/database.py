from motor.motor_asyncio import AsyncIOMotorClient
import datetime

import os
from dotenv import load_dotenv
load_dotenv()

MONGO_DETAILS = os.getenv("MONGO_DETAILS")

# Initialize the client
client = AsyncIOMotorClient(MONGO_DETAILS)

# Create/Connect to the database and collection
database = client.live_neural_landscape
clicks_collection = database.get_collection("clicks")

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