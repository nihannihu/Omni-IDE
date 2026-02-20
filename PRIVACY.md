# 🔒 Privacy Policy — Omni-IDE

> **Effective Date:** February 2026  
> **Last Updated:** February 21, 2026  
> **Maintainer:** Mohammed Nihan

---

## Our Philosophy: Local-First, Always

Omni-IDE is built on a fundamental belief: **your code belongs to you — and only you.** We designed every layer of this application to keep your data on your machine, under your control, with zero telemetry or tracking.

---

## 1. Data We Collect

**None.** Zero. Zilch.

- ❌ We do **not** collect analytics or telemetry data.
- ❌ We do **not** track feature usage, click behavior, or session duration.
- ❌ We do **not** phone home to any server owned by us.
- ❌ We do **not** sell, share, or monetize any user data.

---

## 2. API Keys & Credentials

Your API keys (e.g., HuggingFace) are stored **exclusively on your local machine**:

| Storage Location | Details |
|------------------|---------|
| `.env` file | In your project's `backend/` directory |
| System Environment | Via `HUGGINGFACE_API_KEY` or `HF_TOKEN` |

- Keys are **never** transmitted to us or any third party besides the AI provider you explicitly configure.
- Keys are **never** logged, cached remotely, or persisted outside your machine.
- We strongly recommend adding `.env` to your `.gitignore` (we do this by default).

---

## 3. AI Agent Communication

When you use the built-in AI Agent (chat feature), your prompts and code context are sent **directly** to:

| Provider | Purpose | Your Control |
|----------|---------|-------------|
| **HuggingFace Inference API** | AI code generation & chat | You provide your own API key (BYOK) |

**What is sent:** Your chat message and relevant code context.  
**What is NOT sent:** Your file system contents, browsing history, OS information, or any metadata.

You can disconnect the AI Agent entirely by simply not providing an API key. The IDE's editor, file explorer, terminal, and code execution features work fully offline.

---

## 4. Code Execution

When you click "Run Code," your script is executed **locally** using your system's Python interpreter. No code is sent to any remote server for execution. The execution pipeline operates entirely within `subprocess` on your machine.

---

## 5. Third-Party Dependencies

Omni-IDE uses the following open-source components. Their respective privacy policies apply:

| Component | Purpose | Privacy Note |
|-----------|---------|-------------|
| Monaco Editor (Microsoft) | Code editing | Loaded from CDN; no data sent |
| PyWebView | Desktop window | Local only |
| FastAPI/Uvicorn | Local HTTP server | Runs on `127.0.0.1` only |

---

## 6. Children's Privacy

Omni-IDE does not knowingly collect information from children under 13. The application does not collect information from anyone of any age.

---

## 7. Changes to This Policy

If we ever change our privacy practices, we will update this document and clearly note the changes at the top. Given our local-first architecture, we anticipate minimal changes.

---

## 8. Contact

For privacy inquiries:
- **GitHub Issues:** [github.com/nihannihu/-Omni-IDE/issues](https://github.com/nihannihu/-Omni-IDE/issues)
- **Author:** Mohammed Nihan

---

> **TL;DR:** We collect nothing. Your code stays on your machine. Your API keys stay on your machine. The only external communication is between you and the AI provider you choose to configure.
