# Omni-Agent Studio 🤖

**The Leap to GenAI 2.0: A Localized, Fully Autonomous Digital Worker.**

![Omni-Agent Studio](https://via.placeholder.com/1200x600?text=Omni-Agent+Studio+Demo) 
*(Replace this link with your actual screenshot or demo GIF after pushing)*

## 🚀 Overview
Omni-Agent Studio is not just a chatbot. It is a **localized, voice-controlled AI agent** capable of:
*   **Hearing** your voice in real-time (sub-second latency).
*   **Thinking** through complex problems using Chain-of-Thought.
*   **Writing & Executing** Python code safely to solve tasks.
*   **Seeing** your screen (Experimental VLM integration).
*   **Speaking** back with a typewriter-style interface.

Built to run **100% locally** on consumer hardware (tested on NVIDIA RTX GPU), solving challenges of VRAM spillover and WebSocket concurrency.

## 🛠️ The Tech Stack
*   **Brain:** `smolagents` (Hugging Face) + `Qwen2.5-Coder-1.5B` (4-bit Quantized).
*   **Voice:** `Faster-Whisper` (V3 Turbo) for real-time transcription.
*   **Frontend:** Next.js 14, TypeScript, TailwindCSS, Zustand.
*   **Backend:** FastAPI, WebSockets (`uivcorn`), PyTorch.
*   **Infrastructure:** Docker & Docker Compose.

## ✨ Key Features
*   **Self-Healing Code execution:** The agent writes code, runs it, reads the error, fixes it, and runs it again.
*   **Real-Time Streaming:** Token-by-token streaming from the local LLM to the UI via WebSockets.
*   **System Awareness:** Knows who created it ("Nihan") and respects negative constraints (no hallucinated imports).
*   **Auto-Reconnection:** Robust frontend that heals connections if the backend restarts.

## 📦 Installation

### Option 1: Docker (Recommended)
Run the entire stack with a single command (requires NVIDIA GPU):

```bash
docker-compose up --build
```
Access Frontend at `http://localhost:3000`.

### Option 2: Manual Setup

#### Backend (Python)
1.  Navigate to `backend`:
    ```bash
    cd backend
    python -m venv venv
    .\venv\Scripts\activate  # Windows
    pip install -r requirements.txt
    ```
2.  Run the server:
    ```bash
    uvicorn main:app --reload --port 8000
    ```

#### Frontend (Next.js)
1.  Navigate to `frontend`:
    ```bash
    cd frontend
    npm install
    ```
2.  Run the development server:
    ```bash
    npm run dev
    ```

## 🎥 Demo
Check out the `project_showcase.md` file for script ideas or watch the demo video on my LinkedIn.

## 🤝 Contributing
Built by **Nihan** as a leap into Agentic AI.
Feel free to open issues or PRs!

## 📜 License
MIT
