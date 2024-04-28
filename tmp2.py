import asyncio
import json

import uvicorn
from fastapi import FastAPI, WebSocket, APIRouter
from typing import Dict
import base64
from dotenv import load_dotenv
from src.constants import IMAGE_GET_COOLDOWN_SECONDS
from fastapi.middleware.cors import CORSMiddleware
import os
import base64

load_dotenv()

# Read the image file
with open('data/cat2024-04-27T18:00:40.953638.jpg', 'rb') as img_file:
    # Encode the image file to base64 string
    base64_string = base64.b64encode(img_file.read()).decode('utf-8')

# Print the base64 string
print(base64_string)

