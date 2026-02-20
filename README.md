<p align="center">
  <h1 align="center">🤖 Omni-IDE</h1>
  <p align="center"><strong>The Local AI-Native Code Editor for Python Developers</strong></p>
  <p align="center">
    Build apps 10x faster with integrated autonomous AI agents.<br>
    100% Local. 100% Private. 100% Free.
  </p>
  <p align="center">
    <a href="#installation"><img src="https://img.shields.io/badge/download-latest-brightgreen?style=for-the-badge" alt="Download"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=for-the-badge" alt="MIT License"></a>
    <a href="https://github.com/nihannihu/-Omni-IDE/issues"><img src="https://img.shields.io/badge/support-issues-orange?style=for-the-badge" alt="Issues"></a>
  </p>
</p>

---

## ❓ Why Omni-IDE?

Most AI code editors send your code to the cloud, lock you into subscriptions, and collect your data. **Omni-IDE is different.**

| | Omni-IDE | Cloud AI Editors |
|---|---------|-----------------|
| **Privacy** | 🟢 Your code never leaves your machine | 🔴 Code sent to remote servers |
| **Cost** | 🟢 Free forever (MIT Licensed) | 🔴 $10-40/month subscriptions |
| **Speed** | 🟢 Native desktop app, instant response | 🟡 Network latency on every action |
| **AI Model** | 🟢 BYOK — Bring Your Own Key (HuggingFace) | 🔴 Locked to one provider |
| **Telemetry** | 🟢 Zero data collection | 🔴 Usage tracking & analytics |
| **Offline** | 🟢 Editor + Terminal work fully offline | 🔴 Requires internet for everything |

---

## 🚀 Installation

### Option 1: Download & Run (Recommended)
1. **Download** the latest release from [Releases](https://github.com/nihannihu/-Omni-IDE/releases)
2. **Extract** the `.zip` file
3. **Run** `OmniIDE.exe`
4. Done! No Python, Node.js, or dependencies needed.

### Option 2: Run from Source
```bash
git clone https://github.com/nihannihu/-Omni-IDE.git
cd -Omni-IDE/backend
pip install -r requirements.txt
python desktop.py
```

### AI Setup (Optional)
Create a `.env` file in the `backend/` folder:
```env
HUGGINGFACE_API_KEY=hf_your_key_here
```
> Get a free API key at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

---

## ✨ Features

### 🧠 Autonomous AI Agent
Chat with an AI coding assistant that lives inside your IDE. Ask it to write functions, debug errors, or build entire applications — it writes the code **directly into your editor** automatically.

### 📂 Native File Explorer
Browse your project files with a VS Code-style sidebar. Click folders to drill into subdirectories, navigate with breadcrumb trails, and manage files without leaving the IDE.

### 🖥️ Integrated Terminal
Run Python scripts with one click. See output and errors in a dedicated terminal pane. Supports:
- **Auto-Pip:** Missing a library? The IDE installs it automatically when you run your code
- **GUI Apps:** Pygame and other GUI frameworks launch in the background without freezing the IDE
- **Error Capture:** Full tracebacks displayed with syntax highlighting

### 📝 Monaco Code Editor
The same editor engine that powers VS Code:
- Syntax highlighting for Python, HTML, CSS, JS, and more
- Multi-tab editing with instant context switching
- `Ctrl+S` to save, keyboard shortcuts you already know
- Dark theme optimized for long coding sessions

### 🔒 Privacy-First Architecture
- Zero telemetry, zero tracking, zero data collection
- API keys stored locally in `.env` — never transmitted to us
- AI communication goes directly to HuggingFace (your key, your data)
- Works fully offline (editor, file explorer, terminal)

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Desktop Shell** | PyWebView (Chromium) |
| **Backend** | FastAPI + Uvicorn |
| **Editor** | Monaco Editor |
| **AI Engine** | HuggingFace Inference API via smolagents |
| **Build** | PyInstaller (standalone .exe) |

---

## 🧪 Quality Assurance

Omni-IDE ships with a built-in production audit suite:

```bash
# Automated 6-domain system audit
python production_audit.py

# Automated API test runner (21 tests)
python run_release_tests.py
```

Latest audit: **23 PASS | 0 FAIL** | 🟢 GO

---

## 🤝 Support

- **Bug Reports:** [GitHub Issues](https://github.com/nihannihu/-Omni-IDE/issues)
- **Feature Requests:** [GitHub Issues](https://github.com/nihannihu/-Omni-IDE/issues) (use `enhancement` label)
- **Security:** Please report vulnerabilities via GitHub Issues with the `security` label

---

## 📄 License

[MIT License](LICENSE) — Free to use, modify, and distribute.

Copyright (c) 2026 Mohammed Nihan

---

<p align="center">
  <strong>Built with ❤️ by Mohammed Nihan</strong><br>
  <em>Because developers deserve AI tools that respect their privacy.</em>
</p>
