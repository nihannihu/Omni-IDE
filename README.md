<p align="center">
  <img src="logo.jpeg" alt="Omni-IDE Logo" width="200" />
</p>

# Omni-IDE v3.0.0: The God-Mode Intelligence Update 🚀

Welcome to **Omni-IDE**, a next-generation, agent-first code editor designed for the modern AI era. Built on the rock-solid foundation of VS Code, Omni-IDE is re-engineered to provide a seamless, high-performance environment where AI agents are first-class citizens.

Developed by **Mohammed Nihan (Nihan Nihu)**, a Computer Science student at **VTU**, this project showcases a deep integration of **MERN stack** principles and state-of-the-art **AI Orchestration**.

---

## 🛠️ Cutting-Edge Tech Stack (v3.0.0)

Omni-IDE is built with a focus on performance, scalability, and intelligence:

- **Core Engine**: [TypeScript](https://www.typescriptlang.org/) & [Node.js](https://nodejs.org/)
- **Hybrid Brain**: Integrated with **Google Gemini 3.1 Flash Lite** and **Local Ollama** (Qwen 2.5 Coder) via an intelligent **Multi-Model Fallback Chain**.
- **Frontend Architecture**: High-performance Electron-based workbench with custom UI components.
- **AI Orchestration**: Powered by a custom Python backend using `smolagents` and `litellm`.

---

## 🤖 The "God-Mode" Omni-Agent

The centerpiece of Omni-IDE is the **Omni-Agent**. In v3.0.0, the agent has evolved from a passive assistant to a fully autonomous engineering partner:

- **Self-Healing Code Protocol**: The agent detects terminal errors, analyzes stack traces, and auto-applies code fixes without user intervention.
- **Hardened Security Sandbox**: Advanced path traversal protection ensures the agent can never read or write files outside your sanctioned workspace.
- **Intelligent Intent Routing**: Substring-based intent detection allows the agent to distinguish between "explaining" and "executing" code automatically.
- **Multi-Model Resilience**: Automatically swaps between Gemini 3.1, 3.0, and 2.5 models to bypass API rate limits (429) silently.

---

## 🚀 Building for Production

Omni-IDE uses an optimized Gulp-based build pipeline to ensure the most stable and performant binaries.

### Commands to Build (Windows x64)

1. **Compile & Minify Source**:
   ```powershell
   npm run compile
   ```
2. **Generate Final Installer (.exe)**:
   ```powershell
   npx gulp vscode-win32-x64-user-setup
   ```

The final installer will be located in `.build/win32-x64/user-setup/OmniIDE-Setup.exe`.

---

## 👨‍💻 About the Author

**Mohammed Nihan (Nihan Nihu)** is a passionate Computer Science student and Full-Stack Developer specializing in AI-integrated workflows and experimental IDE architectures.

- **Portfolio**: [nihu.in](https://nihu.in)
- **GitHub**: [@nihannihu](https://github.com/nihannihu)
- **Vision**: To simplify the developer experience by making AI agents as natural as a compiler.

---

## 🛡️ License & Policies

- **License**: [MIT License](LICENSE.txt)
- **Privacy**: [Privacy Policy](PRIVACY_POLICY.md)
- **Security**: [Security Policy](SECURITY.md)

Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.
