# 🐳 Running Omni-Agent Studio with Docker

This guide explains how to run the entire project in a containerized environment, ensuring consistent performance across different systems.

## Prerequisites
1.  **Docker Desktop** installed.
2.  **NVIDIA GPU Drivers** installed (for backend model acceleration).
3.  **NVIDIA Container Toolkit** installed (to allow Docker to see your GPU).

## Quick Start
Open your terminal in the project root (`Omni-Agent-Studio`) and run:

```bash
docker-compose up --build
```

This will:
*   Build the Backend (Python + CUDA)
*   Build the Frontend (Next.js)
*   Start both services.

## Important Notes

### 📊 GPU Support
The `docker-compose.yml` is configured to use your NVIDIA GPU.
If you see errors related to `nvidia-container-runtime`, ensure you have installed the **NVIDIA Container Toolkit**:

```bash
# Windows (WSL2) or Linux
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### 🧠 Model Caching
We mapped a volume `huggingface_cache` so that your heavy AI models (Qwen, Whisper) are **persisted**. You won't have to re-download 5GB+ files every time you restart the container.

### 🌐 Networking
The Frontend connects to the Backend via WebSocket at `ws://localhost:8000/ws/omni`.
Since the browser runs on your host machine (not inside the Docker network), it will access `localhost`. This is why we expose port `8000`.
