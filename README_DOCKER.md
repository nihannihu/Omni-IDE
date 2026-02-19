# 🐳 Running Omni-Agent Studio with Docker (Cloud Brain Edition)

This guide explains how to run the newly upgraded **Omni-Agent Studio** in a lightweight, containerized environment.

## 🚀 Key Upgrades (v2.0)
- **Cloud Brain**: Now powered by `Qwen/Qwen2.5-Coder-32B-Instruct` via serverless API.
- **Lightweight**: No heavy GPU requirements for the main agent! Runs easily on any CPU server.
- **Secure**: Sensitive keys are loaded from `.env`.

## Prerequisites
1.  **Docker Desktop** installed.
2.  Create a `.env` file in `backend/.env` with your `HUGGINGFACE_API_KEY`.
    - Example: `HUGGINGFACE_API_KEY=hf_your_key_here`

## Quick Start
Open your terminal in the project root (`Omni-Agent-Studio`) and run:

```bash
docker-compose up --build
```

This will:
1.  Build the **Backend** (Python 3.11 Slim) - Super fast build!
2.  Build the **Frontend** (Next.js/Node) - Optimized for production.
3.  Start both services.

## Services Access
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **WebSocket**: ws://localhost:8000/ws/omni

## Troubleshooting
### GPU Support (Optional)
The current setup is optimized for CPU efficiency. If you want to use **Local Whisper Transcription** with GPU acceleration:
1.  Uncomment the `deploy: resources: reservations: devices` section in `docker-compose.yml`.
2.  Update `backend/Dockerfile` to use a CUDA-enabled base image (e.g., `pytorch/pytorch:2.1.2-cuda12.1-cudnn8-runtime`) instead of `python:3.11-slim`.
