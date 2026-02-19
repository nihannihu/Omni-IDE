import asyncio
import base64
import json
import logging
import os
import webbrowser
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.concurrency import iterate_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from transcriber import AudioTranscriber
from agent import OmniAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Global instances (to be initialized in lifespan)
transcriber = None
agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern lifespan handler (replaces deprecated @app.on_event)."""
    global transcriber, agent
    logger.info("Initializing models...")
    transcriber = AudioTranscriber()
    agent = OmniAgent()
    logger.info("Models initialized.")
    logger.info("Application startup complete.")
    yield
    logger.info("Application shutting down.")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "online", "agent": "OmniAgent"}

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
                # Run blocking transcription in a separate thread to avoid freezing the WebSocket
                loop = asyncio.get_event_loop()
                text = await loop.run_in_executor(None, transcriber.transcribe, audio_data)
                if text:
                    logger.info(f"Transcribed: {text}")
                    await websocket.send_json({"type": "transcription", "text": text})
                    
                    # Create a new agent log entry on frontend
                    await websocket.send_json({"type": "agent_response_start"})
                    
                    # Normal agent pipeline for all tasks (Smart Router Disabled)
                    try:
                        async for token in iterate_in_threadpool(agent.execute_stream(text)):
                            await websocket.send_json({"type": "agent_token", "text": token})
                            await asyncio.sleep(0.01) 
                    except (WebSocketDisconnect, RuntimeError):
                        logger.info("Client disconnected during streaming")
                        return
                    
                    await websocket.send_json({"type": "agent_response_end"})

            elif "text" in message:
                data = message["text"]
                try:
                    logger.info(f"Message length: {len(data)}")
                    # Check if it's a JSON string
                    payload = json.loads(data)
                    if payload.get("type") == "screen_frame":
                         # Store latest frame for visual queries
                         if "image" in payload:
                             agent.update_vision_context(payload["image"])
                    elif payload.get("type") == "text_input":
                        text = payload.get("text")
                        if text:
                            logger.info(f"Received text input: {text}")
                            await websocket.send_json({"type": "transcription", "text": f"(Text) {text}"})
                            
                            await websocket.send_json({"type": "agent_response_start"})
                            
                            # Normal agent pipeline for all tasks (Smart Router Disabled)
                            try:
                                async for token in iterate_in_threadpool(agent.execute_stream(text)):
                                    await websocket.send_json({"type": "agent_token", "text": token})
                                    await asyncio.sleep(0.01)
                            except (WebSocketDisconnect, RuntimeError):
                                logger.info("Client disconnected during streaming")
                                return
                            await websocket.send_json({"type": "agent_response_end"})
                except json.JSONDecodeError:
                    pass

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error: {e}")
        try:
            await websocket.close()
        except Exception:
            pass
