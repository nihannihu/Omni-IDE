import asyncio
import base64
import json
import logging
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from transcriber import AudioTranscriber
from agent import OmniAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances (to be initialized)
transcriber = None
agent = None

@app.on_event("startup")
async def startup_event():
    global transcriber, agent
    logger.info("Initializing models...")
    transcriber = AudioTranscriber()
    agent = OmniAgent()
    logger.info("Models initialized.")

@app.websocket("/ws/omni")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connected")
    
    try:
        while True:
            # We expect different types of messages:
            # 1. Binary audio chunks (bytes)
            # 2. JSON control messages or image frames (text)
            
            message = await websocket.receive()
            
            if "bytes" in message:
                audio_data = message["bytes"]
                # Process audio
                text = transcriber.transcribe(audio_data)
                if text:
                    logger.info(f"Transcribed: {text}")
                    await websocket.send_json({"type": "transcription", "text": text})
                    
                    # Create a new agent log entry on frontend
                    await websocket.send_json({"type": "agent_response_start"})
                    
                    # Stream tokens
                    for token in agent.execute_stream(text):
                        await websocket.send_json({"type": "agent_token", "text": token})
                        # Small delay to ensure distinct messages if needed, but not strictly necessary
                        await asyncio.sleep(0.01) 
                    
                    await websocket.send_json({"type": "agent_response_end"})

            elif "text" in message:
                data = message["text"]
                try:
                    logger.info(f"Message length: {len(data)}")
                    # Check if it's a JSON string
                    payload = json.loads(data)
                    if payload.get("type") == "screen_frame":
                         # Store latest frame for visual queries
                         # agent.update_vision_context(payload["image"])
                         pass
                    elif payload.get("type") == "text_input":
                        text = payload.get("text")
                        if text:
                            logger.info(f"Received text input: {text}")
                            await websocket.send_json({"type": "transcription", "text": f"(Text) {text}"})
                            
                            await websocket.send_json({"type": "agent_response_start"})
                            # Stream tokens
                            for token in agent.execute_stream(text):
                                await websocket.send_json({"type": "agent_token", "text": token})
                                await asyncio.sleep(0.01)
                            await websocket.send_json({"type": "agent_response_end"})
                except json.JSONDecodeError:
                    pass

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error: {e}")
        await websocket.close()
