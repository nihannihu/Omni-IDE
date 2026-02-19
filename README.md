# Omni-Agent Studio 🤖

**GenAI 2.0: An Autonomous, Voice-Controlled, Production-Ready Digital Worker.**

![Omni-Agent Studio](https://via.placeholder.com/1200x600?text=Omni-Agent+Studio+Cloud+Edition)

## 🚀 Overview
Omni-Agent Studio is a **Cloud-Powered, Autonomous AI Agent** capable of solving complex tasks using state-of-the-art models. This version is optimized for **Production Readiness**, featuring:

*   **Cloud Brain:** Powered by `Qwen2.5-Coder-32B-Instruct` via Hugging Face Serverless API. (No local GPU required for the LLM!)
*   **Vision System:** Real-time screen analysis using the `Qwen2.5-VL-7B` Cloud API. 
*   **Voice Interface:** Sub-second latency transcription via `Faster-Whisper`.
*   **Security Sandbox:** Strict file-system isolation. The agent can only interact with the user's Desktop.
*   **Self-Healing Logic:** The agent writes, tests, and debugs its own Python code autonomously.

## 🛠️ The Tech Stack
*   **Agent Framework:** `smolagents` (Hugging Face).
*   **LLM:** `Qwen2.5-Coder-32B-Instruct` (Cloud Inference).
*   **Vision:** `Qwen2.5-VL-7B-Instruct` (Cloud Inference).
*   **Voice:** `Faster-Whisper` (Local).
*   **Frontend:** Next.js 14, TailwindCSS, TypeScript.
*   **Backend:** FastAPI, WebSockets (`uvicorn`).

## ✨ Key Features
*   **Secure Sandbox**: The agent is restricted from accessing system files and can only operate within a designated sandbox (Desktop).
*   **Real-Time Observations**: Every thought, tool execution, and tool result is streamed directly to the frontend activity log.
*   **Production Hardening**: Removed 10GB+ of local model bloat, switching to lightweight, fast-starting Cloud APIs.
*   **Identity Aware**: Knows its creator (**Nihan Nihu**) and is optimized for the developer's workflow.

## 📦 Installation

### Option 1: Docker (Recommended)
Deployment is simplified via Docker Compose.
1.  Add your `HUGGINGFACE_API_KEY` to `backend/.env`.
2.  Run:
    ```bash
    docker-compose up --build
    ```
3.  Access Frontend at `http://localhost:3000`.

### Option 2: Local Machine
#### Backend (Python)
1.  `cd backend`
2.  `python -m venv venv`
3.  `source venv/bin/activate` (or `.\venv\Scripts\activate` on Windows)
4.  `pip install -r requirements.txt`
5.  Create a `.env` file from `.env.example`.
6.  `python main.py` or `uvicorn main:app --port 8000`

#### Frontend (Next.js)
1.  `cd frontend`
2.  `npm install`
3.  `npm run dev`

## 📜 Security Policy
The agent is designed with a **Safety First** philosophy. It cannot run `os`, `subprocess`, or `pathlib` commands directly. It must use provided `safe_*` wrappers that validate paths against the Sandbox root.

## 🤝 Creator
Built and Optimized for Production by **Nihan Nihu**.
Feel free to open issues or PRs!

## 📜 License
MIT
