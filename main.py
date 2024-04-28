import asyncio
import json

import uvicorn
from fastapi import FastAPI, WebSocket, APIRouter
from typing import Dict
import base64
from dotenv import load_dotenv
from src.constants import IMAGE_GET_COOLDOWN_SECONDS, STORAGE_CLEANUP_COOLDOWN_SECONDS
from fastapi.middleware.cors import CORSMiddleware
from src.image_processor import ImageProcessor
from src.local_storage import LocalStorage
import os

load_dotenv()
app = FastAPI(debug=True)
router = APIRouter()
api_url = os.getenv('IMAGE_API_URL')
if not api_url:
    raise Exception("Please set IMAGE_API_URL environment variable")
image_processor = ImageProcessor(api_url)
storage = LocalStorage(os.getenv('DATA_PATH'))

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
connected_clients: Dict[int, WebSocket] = {}


async def fetch_images():
    while True:
        try:
            print("Fetching images...")
            new_image_data = image_processor.process_new_image()
            print("New image data:", new_image_data)
            if new_image_data:
                storage.save_img(new_image_data)
                updated_image_data = storage.get_images()
                await broadcast_data(json.dumps(updated_image_data))
            await asyncio.sleep(IMAGE_GET_COOLDOWN_SECONDS)
        except Exception as e:
            print(f"An error occurred: {e}")



async def cleanup_storage():
    while True:
        print("Cleaning storage...")
        storage.delete_old_files()
        await asyncio.sleep(STORAGE_CLEANUP_COOLDOWN_SECONDS)


async def broadcast_data(image_data):
    print(connected_clients)
    for client_id, client in connected_clients.items():
        print("Sending image to client:", client_id)
        print(image_data)
        await client.send_text(image_data)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await websocket.accept()
        connected_clients[id(websocket)] = websocket

        while True:
            message = await websocket.receive_text()
            print("Received message from client:", message)
    except Exception as e:
        print("Client disconnected:", e)
    finally:
        del connected_clients[id(websocket)]


@app.get("/hello")
async def hello():
    return {"message": "Image broadcasted successfully."}


@app.get("/recent_images")
async def get_images():
    try:
        response = storage.get_images()
        return response
    except Exception as e:
        print(e)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(fetch_images())
    asyncio.create_task(cleanup_storage())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
