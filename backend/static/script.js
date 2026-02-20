// Omni-IDE Nervous System (script.js)
// v9.0 - Production: Auth Gate, Subfolder Navigation, Agent Bridge

// ═══════════════════════════════════════════
//  AUTHENTICATION GATE (Global Scope)
// ═══════════════════════════════════════════
async function checkAuth() {
    try {
        const response = await fetch('/api/check-auth');
        const data = await response.json();
        const modal = document.getElementById('auth-modal');
        if (!data.authenticated) {
            modal.style.display = 'flex';
            // Focus the input for immediate typing
            setTimeout(() => document.getElementById('api-key-input').focus(), 100);
        } else {
            modal.style.display = 'none';
        }
    } catch (error) {
        console.error("Auth check failed:", error);
    }
}

async function saveApiKey() {
    const input = document.getElementById('api-key-input');
    const key = input.value.trim();
    const errorDiv = document.getElementById('auth-error');
    const btn = document.getElementById('auth-submit-btn');

    // Validate
    if (!key) {
        errorDiv.textContent = '⚠️ Please paste your API key.';
        errorDiv.style.display = 'block';
        input.focus();
        return;
    }
    if (!key.startsWith('hf_')) {
        errorDiv.textContent = '⚠️ Invalid key format — must start with "hf_"';
        errorDiv.style.display = 'block';
        input.focus();
        return;
    }

    // Show loading state
    errorDiv.style.display = 'none';
    const originalText = btn.innerText;
    btn.innerText = '⏳ Connecting...';
    btn.disabled = true;
    btn.style.opacity = '0.7';

    try {
        const response = await fetch('/api/save-key', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key: key })
        });

        if (response.ok) {
            document.getElementById('auth-modal').style.display = 'none';
            // Show success toast if available
            if (typeof showToast === 'function') {
                showToast('✅ Agent Connected! You are ready to code.');
            }
        } else {
            const err = await response.json();
            errorDiv.textContent = '❌ ' + (err.detail || 'Failed to save key.');
            errorDiv.style.display = 'block';
            btn.innerText = originalText;
            btn.disabled = false;
            btn.style.opacity = '1';
        }
    } catch (e) {
        errorDiv.textContent = '❌ Error connecting to server.';
        errorDiv.style.display = 'block';
        btn.innerText = originalText;
        btn.disabled = false;
        btn.style.opacity = '1';
    }
}

// Enter key to submit
document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && document.getElementById('auth-modal').style.display === 'flex') {
        e.preventDefault();
        saveApiKey();
    }
});

// ═══════════════════════════════════════════
//  MAIN IDE INITIALIZATION
// ═══════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
    console.log("Omni-IDE Initializing...");
    checkAuth(); // Run auth gate on startup



    // --- State ---
    const openModels = {};
    let activeFile = null;
    let currentSubpath = ''; // Tracks the current subfolder being browsed

    // --- DOM ---
    const fileListEl = document.getElementById('file-list');
    const changeDirBtn = document.getElementById('change-dir-btn');
    const closeDirBtn = document.getElementById('close-dir-btn');
    const currentPathEl = document.getElementById('current-path');
    const chatInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const chatHistory = document.getElementById('chat-history');
    const statusIndicator = document.querySelector('.status-indicator');
    const runBtn = document.getElementById('run-btn');
    const terminalContent = document.getElementById('terminal-content');
    const terminalClear = document.getElementById('terminal-clear');

    // --- 1. Monaco Editor Init ---
    require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.33.0/min/vs' } });
    require(['vs/editor/editor.main'], function () {
        window.editor = monaco.editor.create(document.getElementById('editor-container'), {
            value: '# Omni-IDE Ready.\n# Select a file or ask the Agent.',
            language: 'python',
            theme: 'vs-dark',
            automaticLayout: true,
            readOnly: true,
            fontSize: 14,
            minimap: { enabled: false }
        });
        console.log("Monaco Editor initialized.");
        updateTabBar();
        window.editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => saveCurrentFile());
    });

    // --- 2. File Explorer Click ---
    fileListEl.addEventListener('click', (e) => {
        const item = e.target.closest('.file-item');
        if (!item) return;
        const name = item.dataset.name;
        const type = item.dataset.type;
        if (!name) return;
        if (type === 'file') {
            // Build the full relative path for opening
            const relativePath = currentSubpath ? currentSubpath + '/' + name : name;
            openFile(relativePath);
        } else if (type === 'directory') {
            // Navigate into the subdirectory
            currentSubpath = currentSubpath ? currentSubpath + '/' + name : name;
            loadFileList();
        }
    });

    // --- 3. Folder Navigation ---
    async function changeDirectory() {
        let cleanPath = null;

        // Native Desktop App mode: Use Pywebview Python Bridge to open a real OS folder dialog
        if (window.pywebview && window.pywebview.api) {
            try {
                const folderPath = await window.pywebview.api.select_folder();
                if (folderPath) {
                    cleanPath = folderPath;
                } else {
                    return; // User canceled the native dialog
                }
            } catch (err) {
                console.error("Native dialog failed:", err);
                // Fallback handled below
            }
        }

        // Browser mode / Fallback: Use manual prompt
        if (!cleanPath) {
            const rawPath = prompt("Enter full path to open (e.g. C:\\Users\\Name\\Project):");
            if (!rawPath) return;
            cleanPath = rawPath.replace(/^["']|["']$/g, '').trim();
        }

        try {
            const response = await fetch('/api/change_dir', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: cleanPath })
            });
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || "Failed to change directory");
            }
            // Clear current state
            Object.keys(openModels).forEach(f => {
                if (openModels[f]) openModels[f].dispose();
                delete openModels[f];
            });
            activeFile = null;
            currentSubpath = ''; // Reset subfolder browsing state
            if (window.editor) window.editor.setValue('# Omni-IDE Ready.\n# Select a file or ask the Agent.');

            updateTabBar();
            loadFileList();
            showToast('📂 Opened: ' + cleanPath);
        } catch (e) {
            showToast('❌ ' + e.message);
        }
    }

    async function closeDirectory() {
        if (!confirm("Close the current folder?")) return;
        try {
            await fetch('/api/close_folder', { method: 'POST' });
            // Clear all state
            Object.keys(openModels).forEach(f => {
                if (openModels[f]) openModels[f].dispose();
                delete openModels[f];
            });
            activeFile = null;
            currentSubpath = ''; // Reset subfolder browsing state
            if (window.editor) window.editor.setValue('# Omni-IDE Ready.\n# No folder open.');

            updateTabBar();
            loadFileList();
            showToast('🔒 Folder closed.');
        } catch (e) {
            console.error(e);
            showToast('❌ Error closing folder');
        }
    }

    if (changeDirBtn) changeDirBtn.addEventListener('click', changeDirectory);
    if (closeDirBtn) closeDirBtn.addEventListener('click', closeDirectory);

    // --- 4. File System ---
    async function loadFileList() {
        fileListEl.innerHTML = '<div class="file-item loading">Loading...</div>';
        try {
            const url = currentSubpath
                ? `/api/files?subpath=${encodeURIComponent(currentSubpath)}`
                : '/api/files';
            const response = await fetch(url);
            const data = await response.json();
            if (data.no_directory) {
                currentPathEl.textContent = '';
                closeDirBtn.style.display = 'none'; // Hide close button
                fileListEl.innerHTML = '<div style="padding:20px;text-align:center;color:#888;font-size:13px;line-height:1.6;"><div style="font-size:28px;margin-bottom:10px;">&#128194;</div>No folder open.<br>Click <b>Open Folder</b> above to get started.</div>';
                return;
            }
            if (data.current_dir) {
                // Show full browsing path with subpath
                const displayPath = currentSubpath
                    ? data.current_dir + '/' + currentSubpath
                    : data.current_dir;
                currentPathEl.textContent = displayPath;
                closeDirBtn.style.display = 'block'; // Show close button
            }
            fileListEl.innerHTML = '';

            // --- Breadcrumb Navigation ---
            if (currentSubpath) {
                // Build clickable breadcrumb trail
                const breadcrumbDiv = document.createElement('div');
                breadcrumbDiv.style.cssText = 'padding:6px 12px;font-size:11px;color:#888;border-bottom:1px solid #333;display:flex;align-items:center;gap:4px;flex-wrap:wrap;';

                // Root link
                const rootLink = document.createElement('span');
                rootLink.textContent = '📁 Root';
                rootLink.style.cssText = 'cursor:pointer;color:#4fc3f7;';
                rootLink.onclick = () => { currentSubpath = ''; loadFileList(); };
                breadcrumbDiv.appendChild(rootLink);

                // Build breadcrumb segments
                const parts = currentSubpath.split('/');
                parts.forEach((part, i) => {
                    const sep = document.createElement('span');
                    sep.textContent = ' › ';
                    sep.style.color = '#555';
                    breadcrumbDiv.appendChild(sep);

                    const link = document.createElement('span');
                    link.textContent = part;
                    if (i < parts.length - 1) {
                        // Clickable parent segment
                        link.style.cssText = 'cursor:pointer;color:#4fc3f7;';
                        const targetPath = parts.slice(0, i + 1).join('/');
                        link.onclick = () => { currentSubpath = targetPath; loadFileList(); };
                    } else {
                        // Current directory (not clickable)
                        link.style.cssText = 'color:#ccc;font-weight:bold;';
                    }
                    breadcrumbDiv.appendChild(link);
                });

                fileListEl.appendChild(breadcrumbDiv);

                // Back / Parent button
                const backDiv = document.createElement('div');
                backDiv.className = 'file-item directory';
                backDiv.style.cssText = 'display:flex;align-items:center;cursor:pointer;color:#4fc3f7;font-weight:bold;';
                backDiv.textContent = '⬆️ ..';
                backDiv.title = 'Go up one level';
                backDiv.onclick = () => {
                    const parts = currentSubpath.split('/');
                    parts.pop();
                    currentSubpath = parts.join('/');
                    loadFileList();
                };
                fileListEl.appendChild(backDiv);
            }

            if (data.files && data.files.length > 0) {
                data.files.forEach(file => {
                    const div = document.createElement('div');
                    div.className = 'file-item ' + file.type;
                    div.dataset.name = file.name;
                    div.dataset.type = file.type;
                    div.style.display = 'flex';
                    div.style.justifyContent = 'space-between';
                    div.style.alignItems = 'center';

                    const nameSpan = document.createElement('span');
                    nameSpan.textContent = (file.type === 'directory' ? '📁 ' : '📄 ') + file.name;
                    nameSpan.style.flex = '1';
                    nameSpan.style.overflow = 'hidden';
                    nameSpan.style.textOverflow = 'ellipsis';
                    div.appendChild(nameSpan);

                    if (file.type === 'file') {
                        const delBtn = document.createElement('span');
                        delBtn.textContent = '🗑️';
                        delBtn.className = 'file-delete-btn';
                        delBtn.title = 'Delete ' + file.name;
                        delBtn.style.cssText = 'cursor:pointer;opacity:0.4;font-size:12px;padding:2px 4px;margin-left:4px;';
                        delBtn.onmouseenter = () => { delBtn.style.opacity = '1'; };
                        delBtn.onmouseleave = () => { delBtn.style.opacity = '0.4'; };
                        const fullRelPath = currentSubpath ? currentSubpath + '/' + file.name : file.name;
                        delBtn.onclick = (ev) => { ev.stopPropagation(); deleteFile(fullRelPath); };
                        div.appendChild(delBtn);
                    }

                    fileListEl.appendChild(div);
                });
            } else {
                fileListEl.innerHTML += '<div class="file-item" style="color:#666;font-style:italic;">Empty folder</div>';
            }
        } catch (e) {
            fileListEl.innerHTML = '<div class="file-item error">Connection Failed</div>';
        }
    }

    // *** RELIABLE DELETE: Direct REST API call (not LLM-dependent) ***
    async function deleteFile(filename) {
        if (!confirm('Delete "' + filename + '"? This cannot be undone.')) return;
        try {
            const response = await fetch('/api/delete?filename=' + encodeURIComponent(filename), {
                method: 'DELETE'
            });
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Delete failed');
            }
            showToast('\ud83d\uddd1\ufe0f Deleted: ' + filename);
            closeTab(filename, null);
            loadFileList();
        } catch (e) {
            showToast('\u274c Delete failed: ' + e.message);
        }
    }

    async function openFile(filename) {
        if (openModels[filename]) { switchToTab(filename); return; }
        try {
            const response = await fetch('/api/read?filename=' + encodeURIComponent(filename));
            if (!response.ok) throw new Error("File not found");
            const data = await response.json();
            const ext = filename.split('.').pop().toLowerCase();
            const langMap = { html: 'html', css: 'css', js: 'javascript', json: 'json', md: 'markdown', txt: 'plaintext', py: 'python' };
            const lang = langMap[ext] || 'plaintext';
            openModels[filename] = monaco.editor.createModel(data.content, lang);
            switchToTab(filename);
        } catch (e) {
            showToast('❌ Could not open: ' + filename);
        }
    }

    // *** CRITICAL: Reload a file that was modified by the agent ***
    async function reloadFile(filename) {
        try {
            const response = await fetch('/api/read?filename=' + encodeURIComponent(filename));
            if (!response.ok) return;
            const data = await response.json();
            if (openModels[filename]) {
                // Update existing model in-place (preserves tab state)
                openModels[filename].setValue(data.content);
                console.log('Reloaded: ' + filename);
            } else {
                // Not open yet — open it fresh
                const ext = filename.split('.').pop().toLowerCase();
                const langMap = { html: 'html', css: 'css', js: 'javascript', json: 'json', md: 'markdown', txt: 'plaintext', py: 'python' };
                openModels[filename] = monaco.editor.createModel(data.content, langMap[ext] || 'plaintext');
            }
            switchToTab(filename);
        } catch (e) {
            console.error('Reload error: ' + filename, e);
        }
    }

    // *** Reload ALL open tabs (fallback when we don't know which files changed) ***
    async function reloadAllOpenFiles() {
        const filesToReload = Object.keys(openModels);
        for (const fname of filesToReload) {
            await reloadFile(fname);
        }
    }

    // --- 5. Tabs ---
    function switchToTab(filename) {
        if (!window.editor || !openModels[filename]) return;
        window.editor.setModel(openModels[filename]);
        window.editor.updateOptions({ readOnly: false });
        activeFile = filename;
        updateTabBar();
    }

    function closeTab(filename, e) {
        if (e) e.stopPropagation();
        if (openModels[filename]) { openModels[filename].dispose(); delete openModels[filename]; }
        if (activeFile === filename) {
            activeFile = null;
            const remaining = Object.keys(openModels);
            if (remaining.length > 0) switchToTab(remaining[remaining.length - 1]);
            else setEmptyState();
        }
        updateTabBar();
    }

    function setEmptyState() {
        if (window.editor) {
            window.editor.setModel(monaco.editor.createModel('# Omni-IDE Ready.\n# Select a file or ask the Agent.', 'python'));
            window.editor.updateOptions({ readOnly: true });
        }
        activeFile = null;
    }

    function updateTabBar() {
        const tabBar = document.getElementById('tab-bar');
        if (!tabBar) return;
        tabBar.innerHTML = '';
        Object.keys(openModels).forEach(filename => {
            const tab = document.createElement('div');
            tab.className = 'tab' + (filename === activeFile ? ' active' : '');
            const name = document.createElement('span');
            name.className = 'tab-name';
            name.textContent = filename;
            const close = document.createElement('span');
            close.className = 'tab-close';
            close.textContent = '\u00d7';
            close.onclick = (ev) => closeTab(filename, ev);
            tab.appendChild(name);
            tab.appendChild(close);
            tab.onclick = () => switchToTab(filename);
            tabBar.appendChild(tab);
        });
    }

    // --- 6. Chat ---
    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;
        appendMessage('user', text);
        chatInput.value = '';
        chatInput.disabled = true;
        sendBtn.disabled = true;
        sendBtn.textContent = '\u23f3';
        const thinkingId = showThinking();

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            });
            removeThinking(thinkingId);
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Error ' + response.status);
            }
            const data = await response.json();
            const reply = data.response || 'Task completed.';
            appendMessage('assistant', reply);
            handleAgentResponse(reply);
        } catch (e) {
            removeThinking(thinkingId);
            appendMessage('system', '\u274c Error: ' + e.message);
        } finally {
            chatInput.disabled = false;
            sendBtn.disabled = false;
            sendBtn.textContent = 'Send';
            chatInput.focus();
        }
    }

    // *** PRODUCTION FIX: Resilient response handler ***
    function handleAgentResponse(reply) {
        const replyLower = reply.toLowerCase();

        // Pattern 0: "DELETED: file1.html, file2.css" — close tabs + refresh
        const deleteMatch = reply.match(/DELETED:\s*(.+)/i);
        if (deleteMatch) {
            const fileNames = deleteMatch[1].split(',')
                .map(f => f.trim().replace(/['"\.!]+$/, '').trim())
                .filter(f => f.length > 0 && f.includes('.'));
            fileNames.forEach(fname => closeTab(fname, null));
            showToast('\ud83d\uddd1\ufe0f ' + fileNames.length + ' file(s) deleted!');
            setTimeout(() => loadFileList(), 300);
            return;
        }

        // Pattern 1: "DONE: file1.html, file2.css" — extract specific filenames
        const doneMatch = reply.match(/DONE:\s*(.+)/i);
        const filesMatch = reply.match(/FILES_CREATED:\s*(.+)/i);

        if (doneMatch || filesMatch) {
            const fileStr = (doneMatch && doneMatch[1]) || (filesMatch && filesMatch[1]);
            const fileNames = fileStr.split(',')
                .map(f => f.trim().replace(/['"\.!]+$/, '').trim())
                .filter(f => f.length > 0 && f.includes('.'));

            if (fileNames.length > 0) {
                showToast('\u2705 ' + fileNames.length + ' file(s) updated!');
                setTimeout(() => loadFileList(), 300);
                setTimeout(() => {
                    fileNames.forEach(fname => {
                        console.log('Reloading: ' + fname);
                        reloadFile(fname);
                    });
                }, 600);
                return;
            }
        }

        // Pattern 2: Any "done"/"completed"/"modified" without filenames → reload ALL open tabs
        if (replyLower.includes('done') || replyLower.includes('completed') ||
            replyLower.includes('created') || replyLower.includes('modified') ||
            replyLower.includes('updated') || replyLower.includes('written') ||
            replyLower.includes('saved')) {
            showToast('\ud83d\udd04 Agent finished. Refreshing all files...');
            setTimeout(() => loadFileList(), 300);
            setTimeout(() => reloadAllOpenFiles(), 600);
            return;
        }

        // Pattern 3: Code blocks → inject into editor
        const codeBlocks = extractAllCodeBlocks(reply);
        if (codeBlocks.length > 0) {
            const best = codeBlocks[codeBlocks.length - 1];
            if (window.editor) {
                if (activeFile) {
                    window.editor.setValue(best.code);
                    showToast('\ud83d\udc89 Code injected into ' + activeFile);
                } else {
                    const ext = langToExt(best.lang || 'python');
                    const scratch = 'scratch.' + ext;
                    if (openModels[scratch]) { openModels[scratch].dispose(); delete openModels[scratch]; }
                    openModels[scratch] = monaco.editor.createModel(best.code, best.lang || 'python');
                    switchToTab(scratch);
                    showToast('\ud83d\udc89 Code loaded into ' + scratch);
                }
            }
        }
    }

    function extractAllCodeBlocks(text) {
        const regex = /```(\w+)?\s*\n?([\s\S]*?)```/g;
        const blocks = [];
        let match;
        while ((match = regex.exec(text)) !== null) {
            if (match[2].includes('safe_write(') || match[2].includes('final_answer(')) continue;
            blocks.push({ lang: match[1] || 'python', code: match[2].trim() });
        }
        return blocks;
    }

    function langToExt(lang) {
        return { python: 'py', javascript: 'js', html: 'html', css: 'css', json: 'json', markdown: 'md' }[lang] || 'txt';
    }

    function appendMessage(role, text) {
        const div = document.createElement('div');
        div.className = 'message ' + role;
        const bubble = document.createElement('div');
        bubble.className = 'bubble';
        bubble.textContent = text;
        if (text.includes('DONE:') || text.includes('safe_write')) {
            bubble.style.fontFamily = "'Cascadia Code', 'Fira Code', monospace";
            bubble.style.fontSize = '12px';
            bubble.style.whiteSpace = 'pre-wrap';
        }
        div.appendChild(bubble);
        chatHistory.appendChild(div);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function showThinking() {
        const id = 'thinking-' + Date.now();
        const div = document.createElement('div');
        div.id = id;
        div.className = 'message assistant';
        const bubble = document.createElement('div');
        bubble.className = 'bubble thinking';
        bubble.textContent = '\u23f3 Agent thinking...';
        bubble.style.fontStyle = 'italic';
        bubble.style.opacity = '0.7';
        div.appendChild(bubble);
        chatHistory.appendChild(div);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        return id;
    }

    function removeThinking(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    sendBtn.addEventListener('click', sendMessage);
    // Textarea: Enter sends, Shift+Enter inserts newline (ChatGPT-style)
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    // Auto-grow textarea as user types
    chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = Math.min(chatInput.scrollHeight, 80) + 'px';
    });

    // --- 7. Run Button ---
    if (terminalClear) {
        terminalClear.addEventListener('click', () => {
            terminalContent.textContent = "Waiting for output...";
            terminalContent.style.color = "#d4d4d4";
        });
    }

    if (runBtn) {
        runBtn.addEventListener('click', async () => {
            if (!window.editor || !activeFile) { showToast("Open a file first."); return; }
            const ext = activeFile.split('.').pop().toLowerCase();

            if (ext === 'html') {
                await saveCurrentFile();
                terminalContent.textContent = '\ud83c\udf10 Opening ' + activeFile + ' preview...';
                terminalContent.style.color = "#4caf50";
                window.open('/workspace/' + encodeURIComponent(activeFile), '_blank');
                showToast('\ud83c\udf10 Previewing ' + activeFile);
                return;
            }
            if (ext !== 'py') {
                terminalContent.textContent = '\u26a0\ufe0f Cannot execute .' + ext + ' files. Only .py files can be run.';
                terminalContent.style.color = "#ffaa00";
                showToast('\u26a0\ufe0f Only .py files are executable');
                return;
            }
            await saveCurrentFile();
            runBtn.textContent = "\u23f3 Running...";
            runBtn.disabled = true;
            terminalContent.textContent = 'Running ' + activeFile + '...';
            terminalContent.style.color = "#888";
            try {
                const code = window.editor.getValue();
                const res = await (await fetch('/api/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code: code })
                })).json();
                let out = '';
                if (res.stdout) out += res.stdout;
                if (res.stderr) out += '\n[STDERR]\n' + res.stderr;
                terminalContent.textContent = out || '\u2705 Success (No Output)';
                terminalContent.style.color = res.returncode !== 0 ? '#ff6b6b' : '#4caf50';
            } catch (e) {
                terminalContent.textContent = 'Error: ' + e.message;
                terminalContent.style.color = '#ff6b6b';
            } finally {
                runBtn.textContent = '\u25b6 Run Code';
                runBtn.disabled = false;
            }
        });
    }

    // --- 8. Save ---
    async function saveCurrentFile() {
        if (!activeFile || !window.editor) return;
        try {
            const code = window.editor.getValue();
            const response = await fetch('/api/save?filename=' + encodeURIComponent(activeFile), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: code })
            });
            if (!response.ok) throw new Error("Save failed");
            showToast('\ud83d\udcbe Saved ' + activeFile);
        } catch (e) {
            showToast('\u274c Save failed: ' + e.message);
        }
    }

    // --- 9. Toast ---
    function showToast(msg) {
        let toast = document.getElementById('toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'toast';
            toast.style.cssText = 'position:fixed;bottom:20px;right:20px;background:#1a1a2e;color:#e0e0e0;padding:12px 24px;border-radius:8px;z-index:9999;transition:opacity 0.5s;font-size:13px;box-shadow:0 4px 16px rgba(0,0,0,0.4);border:1px solid #333;';
            document.body.appendChild(toast);
        }
        toast.textContent = msg;
        toast.style.opacity = '1';
        toast.style.display = 'block';
        setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => { toast.style.display = 'none'; }, 500); }, 3000);
    }

    // --- 10. Heartbeat ---
    async function checkConnection() {
        try {
            const r = await fetch('/health');
            if (r.ok) { statusIndicator.classList.add('online'); }
            else throw new Error();
        } catch { statusIndicator.classList.remove('online'); }
    }

    // --- Boot ---
    loadFileList();
    checkConnection();
    setInterval(checkConnection, 5000);
    console.log("Omni-IDE Ready.");
});
