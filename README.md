<p align="center">
  <img src="logo.jpeg" alt="Omni-IDE Logo" width="200" />
</p>

# Omni-IDE v2.0: The AI-Powered Developer Workspace 🚀

Welcome to **Omni-IDE**, a next-generation, agent-first code editor designed for the modern AI era. Built on the rock-solid foundation of VS Code, Omni-IDE is re-engineered to provide a seamless, high-performance environment where AI agents are first-class citizens.

Developed by **Mohammed Nihan (Nihan Nihu)**, a Computer Science student at **VTU**, this project showcases a deep integration of **MERN stack** principles and state-of-the-art **AI Orchestration**.

---

## 🛠️ Cutting-Edge Tech Stack

Omni-IDE is built with a focus on performance, scalability, and intelligence:

- **Core Engine**: [TypeScript](https://www.typescriptlang.org/) & [Node.js](https://nodejs.org/)
- **Frontend Architecture**: High-performance Electron-based workbench with custom UI components.
- **AI Brain**: Integrated with [Google Gemini API](https://ai.google.dev/) for advanced reasoning and code generation.
- **Extensibility**: Full support for the Open VSX Ecosystem.

---

## 🤖 Meet the Omni-Agent

The centerpiece of Omni-IDE is the **Omni-Agent**. Unlike standard "chatbots," Omni-Agent is a deeply integrated AI partner that assists across the entire development lifecycle:

- **Intelligent Refactoring**: Suggests architectural improvements based on best practices.
- **Context-Aware Debugging**: Analyzes runtime errors and proposes validated fixes.
- **Automated Documentation**: Generates high-quality documentation for your complex modules instantly.
- **Project Management**: Helps you track tasks and manage your codebase through natural language.

---

## 🚀 Building for Production

Omni-IDE uses an optimized Gulp-based build pipeline to ensure the most stable and performant binaries.

### Commands to Build (Windows x64)

1. **Clean & Minify Source**:
   ```powershell
   npx gulp vscode-win32-x64-min
   ```
2. **Generate Native Updater**:
   ```powershell
   npx gulp vscode-win32-x64-inno-updater
   ```
3. **Generate Final Installer (.exe)**:
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
