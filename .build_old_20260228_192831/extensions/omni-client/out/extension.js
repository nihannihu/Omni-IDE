"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function (o, m, k, k2) {
	if (k2 === undefined) k2 = k;
	var desc = Object.getOwnPropertyDescriptor(m, k);
	if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
		desc = { enumerable: true, get: function () { return m[k]; } };
	}
	Object.defineProperty(o, k2, desc);
}) : (function (o, m, k, k2) {
	if (k2 === undefined) k2 = k;
	o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function (o, v) {
	Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function (o, v) {
	o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
	var ownKeys = function (o) {
		ownKeys = Object.getOwnPropertyNames || function (o) {
			var ar = [];
			for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
			return ar;
		};
		return ownKeys(o);
	};
	return function (mod) {
		if (mod && mod.__esModule) return mod;
		var result = {};
		if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
		__setModuleDefault(result, mod);
		return result;
	};
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const cp = __importStar(require("child_process"));
const path = __importStar(require("path"));
let pythonProcess;
let outputChannel;
async function activate(context) {
	console.log("Omni-Agent: Activation Started!");
	outputChannel = vscode.window.createOutputChannel("Omni-Agent");
	outputChannel.appendLine("Omni-Agent Activating (UTF-8 Mode)...");
	const config = vscode.workspace.getConfiguration('omni-agent');
	const userPython = config.get('pythonPath');
	let pythonCommand = userPython || 'python';
	try {
		cp.execSync(`${pythonCommand} --version`);
	}
	catch {
		if (!userPython) {
			pythonCommand = 'python3';
			try {
				cp.execSync('python3 --version');
			}
			catch {
				pythonCommand = 'python';
			}
		}
	}
	const backendPath = path.join(context.extensionPath, 'backend', 'main.py');
	outputChannel.appendLine(`Backend Path: ${backendPath}`);
	outputChannel.appendLine(`Python Command: ${pythonCommand}`);
	const env = { ...process.env, PYTHONIOENCODING: 'utf-8' };
	pythonProcess = cp.spawn(pythonCommand, [backendPath], { env });
	pythonProcess.stdout?.on('data', (data) => {
		outputChannel.appendLine(`[Backend]: ${data}`);
	});
	pythonProcess.stderr?.on('data', (data) => {
		const msg = data.toString();
		outputChannel.appendLine(`[Backend Log]: \`);
	});
	pythonProcess.on('error', (err) => {
		vscode.window.showErrorMessage(`Failed to start Python: ${err.message}`);
	});
	const provider = new OmniChatProvider(context.extensionUri, context.secrets, context);
	context.subscriptions.push(vscode.window.registerWebviewViewProvider('omni-client.chatView', provider, {
		webviewOptions: {
			retainContextWhenHidden: true
		}
	}));
	context.subscriptions.push(vscode.commands.registerCommand('omni-client.start', () => {
		vscode.window.showInformationMessage('Omni Agent is running!');
	}), vscode.commands.registerCommand('omni-client.openChat', () => {
		vscode.commands.executeCommand('omni-client.chatView.focus');
	}), vscode.commands.registerCommand('omni.setGeminiKey', async () => {
		const key = await vscode.window.showInputBox({
			title: "Setup Omni Intelligence",
			prompt: "Enter Gemini API Key (Starts with 'AIza...')",
			placeHolder: "Paste your key here to enable Cloud Mode",
			password: true,
			ignoreFocusOut: true,
		});
		if (key && key.startsWith("AIza")) {
			await context.secrets.store('omni_gemini_key', key);
			await context.globalState.update('omni_ask_for_key', true);
			vscode.window.showInformationMessage("Cloud Mode Activated!");
			vscode.commands.executeCommand('workbench.action.reloadWindow');
		}
		else if (key) {
			vscode.window.showErrorMessage("Invalid Key. Must start with 'AIza'.");
		}
	}), vscode.commands.registerCommand('omni.resetKey', async () => {
		await context.secrets.delete('omni_gemini_key');
		await context.globalState.update('omni_ask_for_key', true);
		vscode.window.showInformationMessage("API Key Cleared. Restarting...");
		vscode.commands.executeCommand('workbench.action.reloadWindow');
	}));
	setTimeout(async () => {
		console.log("Omni-Agent: Running Startup Check...");
		try {
			await vscode.commands.executeCommand('omni-client.chatView.focus');
		} catch (e) {
			console.warn("Omni-Agent: Could not auto-focus chat view:", e);
		}
		const secretKey = await context.secrets.get('omni_gemini_key');
		const isValidKey = !!(secretKey && secretKey.length >= 30 && secretKey.startsWith("AIza"));
		if (!isValidKey) {
			outputChannel.appendLine("Triggering setup prompt (every startup until key is set)...");
			if (provider._view) {
				provider.showSetupPrompt("Setup Gemini for the best experience! Or use Ollama for free.");
			}
			vscode.window.showWarningMessage(
				"Omni-IDE: Unlock full AI power with Gemini! Setup now?",
				"Enter Key",
				"Remind Me Later"
			).then(async (selection) => {
				if (selection === "Enter Key") {
					vscode.commands.executeCommand('omni.setGeminiKey');				}
			});
		} else {
			outputChannel.appendLine("Startup Check Passed - Gemini key is valid.");
		}
	}, 4000);
}
class OmniChatProvider {
	_extensionUri;
	_secrets;
	_context;
	_view;
	constructor(_extensionUri, _secrets, _context) {
		this._extensionUri = _extensionUri;
		this._secrets = _secrets;
		this._context = _context;
	}
	resolveWebviewView(webviewView) {
		this._view = webviewView;
		webviewView.description = "Omni-Agent Session";
		webviewView.webview.options = {
			enableScripts: true,
			localResourceRoots: [this._extensionUri]
		};
		webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);
		webviewView.webview.onDidReceiveMessage(async (data) => {
			if (data.command === 'openSettings') {
				vscode.commands.executeCommand('omni.setGeminiKey');
			}
			else if (data.command === 'sendChat') {
				await this.handleSendChat(data.text, webviewView);
			}
			else if (data.command === 'openUrl') {
				vscode.env.openExternal(vscode.Uri.parse(data.url));
			}
			else if (data.command === 'runTerminalCommand') {
				const terminalName = "Omni-Setup";
				let terminal = vscode.window.terminals.find(t => t.name === terminalName);
				if (!terminal) {
					terminal = vscode.window.createTerminal(terminalName);
				}
				terminal.show();
				terminal.sendText(data.text);
			}
		});
		webviewView.show?.(true);
	}
	showSetupPrompt(reason) {
		if (this._view) {
			this._view.webview.postMessage({ command: 'showSetupPrompt', text: reason });
		}
	}
	async handleSendChat(text, webviewView) {
		const activeEditor = vscode.window.activeTextEditor;
		const workspaceFolders = vscode.workspace.workspaceFolders;
		const projectRoot = workspaceFolders ? workspaceFolders[0].uri.fsPath : "";
		const currentFile = activeEditor ? activeEditor.document.fileName : "";
		const fileContent = activeEditor ? activeEditor.document.getText() : "";
		const apiKey = await this._secrets.get('omni_gemini_key');
		try {
			const healthCheck = await fetch('http://127.0.0.1:7860/api/health', {
				signal: AbortSignal.timeout(5000)
			});
			if (!healthCheck.ok) throw new Error('Backend unhealthy');
		}
		catch (healthErr) {
			webviewView.webview.postMessage({
				command: 'receiveResponse',
				text: "Python Backend Not Running. The Omni-Agent backend is not reachable. Check the Omni-Agent output channel (View > Output > Omni-Agent) for details."
			});
			return;
		}
		webviewView.webview.postMessage({ command: 'startLoading' });
		const controller = new AbortController();
		const timeoutId = setTimeout(() => controller.abort(), 600000);
		try {
			const response = await fetch('http://127.0.0.1:7860/api/chat', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'X-Gemini-Key': apiKey || ''
				},
				body: JSON.stringify({
					text,
					context: fileContent,
					filePath: currentFile,
					projectPath: projectRoot
				}),
				signal: controller.signal
			});
			const resData = await response.json();
			if (resData.cloud_status === "error") {
				const errorType = resData.cloud_error === "QUOTA_EXCEEDED" ? "Quota Exceeded" : "Invalid Key";
				this.showSetupPrompt(`Omni Cloud Error: ${errorType}. Switch models or update key?`);
			}
			webviewView.webview.postMessage({
				command: 'receiveResponse',
				text: resData.response || resData.message || "Brain responded.",
				error_type: resData.error_type,
				command_text: resData.command
			});
			if (resData.fileChanged) {
				vscode.commands.executeCommand('workbench.action.files.revert');
			}
		}
		catch (err) {
			const errorMsg = err.name === 'AbortError'
				? "Request Timed Out (10 min). The AI is taking too long. Try breaking your task into smaller steps, or try again in a moment."
				: "Connection Error: " + err.message;
			webviewView.webview.postMessage({
				command: 'receiveResponse',
				text: errorMsg
			});
		}
		finally {
			clearTimeout(timeoutId);
		}
	}
	_getHtmlForWebview(webview) {
		return `<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    font-family: var(--vscode-font-family);
                    background-color: var(--vscode-editor-background);
                    color: var(--vscode-editor-foreground);
                    padding: 0; margin: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden;
                }
                .chat-container { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 12px; }
                .message { max-width: 85%; padding: 10px 14px; border-radius: 12px; font-size: 13px; line-height: 1.5; word-wrap: break-word; }
                .onboarding-card {
                    background: linear-gradient(135deg, var(--vscode-editorWidget-background), var(--vscode-editor-background));
                    border: 1px solid var(--vscode-widget-border);
                    border-left: 4px solid #4fc3f7;
                    padding: 16px; border-radius: 8px; margin: 8px 0;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                }
                .onboarding-card h3 { margin: 0 0 12px 0; font-size: 15px; color: #4fc3f7; }
                .onboarding-card .mode-item {
                    display: flex; align-items: flex-start; gap: 8px;
                    padding: 8px 0; border-bottom: 1px solid var(--vscode-widget-border);
                    font-size: 12px; line-height: 1.6;
                }
                .onboarding-card .mode-item:last-child { border-bottom: none; }
                .onboarding-card .mode-icon { font-size: 16px; min-width: 24px; text-align: center; }
                .onboarding-card .mode-label { font-weight: 600; color: var(--vscode-editor-foreground); }
                .onboarding-card .mode-desc { color: var(--vscode-descriptionForeground); }
                .onboarding-card .try-text {
                    margin-top: 12px; padding: 8px 12px;
                    background: var(--vscode-editor-inactiveSelectionBackground);
                    border-radius: 6px; font-size: 12px; font-style: italic;
                    color: var(--vscode-editor-foreground);
                }
                .setup-card {
                    background: var(--vscode-editorWidget-background);
                    border: 1px solid var(--vscode-widget-border);
                    border-left: 4px solid var(--vscode-notificationsWarningIcon-foreground);
                    padding: 15px; border-radius: 4px; margin: 10px 0; box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                }
                .setup-card h3 { margin: 0 0 10px 0; font-size: 14px; }
                .setup-card p { margin: 0 0 15px 0; font-size: 12px; color: var(--vscode-descriptionForeground); }
                .setup-btns { display: flex; gap: 8px; flex-wrap: wrap; }
                .setup-btns button {
                    background: var(--vscode-button-background); color: var(--vscode-button-foreground);
                    border: none; padding: 6px 12px; cursor: pointer; border-radius: 2px; font-size: 11px;
                }
                .setup-btns button:hover { background: var(--vscode-button-hoverBackground); }
                .setup-btns button.secondary { background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground); }
                .error-card {
                    background: var(--vscode-editorMarkerNavigationError-background);
                    border: 1px solid var(--vscode-editorError-foreground);
                    padding: 12px; border-radius: 8px; margin: 8px 0; border-left: 4px solid var(--vscode-editorError-foreground);
                }
                .warning-card {
                    background: var(--vscode-editorMarkerNavigationWarning-background);
                    border: 1px solid var(--vscode-editorWarning-foreground);
                    padding: 12px; border-radius: 8px; margin: 8px 0; border-left: 4px solid var(--vscode-editorWarning-foreground);
                }
                .btn-install {
                    background-color: var(--vscode-button-background); color: var(--vscode-button-foreground);
                    border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; width: 100%; font-weight: bold; margin-top: 8px;
                }
                .btn-install:hover { background-color: var(--vscode-button-hoverBackground); }
                .btn-install:disabled { opacity: 0.5; cursor: not-allowed; }
                .user { align-self: flex-end; background-color: var(--vscode-button-background); color: var(--vscode-button-foreground); border-bottom-right-radius: 2px; }
                .ai { align-self: flex-start; background-color: var(--vscode-editor-inactiveSelectionBackground); color: var(--vscode-editor-foreground); border-bottom-left-radius: 2px; border: 1px solid var(--vscode-widget-border); }
                .input-area { padding: 15px; background-color: var(--vscode-editor-background); border-top: 1px solid var(--vscode-widget-border); display: flex; gap: 10px; }
                textarea { flex: 1; background-color: var(--vscode-input-background); color: var(--vscode-input-foreground); border: 1px solid var(--vscode-input-border); border-radius: 6px; padding: 8px; resize: none; height: 40px; font-family: inherit; outline: none; }
                textarea:focus { border-color: var(--vscode-focusBorder); }
                button { background-color: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; border-radius: 6px; padding: 0 15px; cursor: pointer; font-weight: 600; }
                button:hover { background-color: var(--vscode-button-hoverBackground); }
                .thinking-container { display: none; align-items: center; gap: 8px; padding: 10px 15px; margin-bottom: 10px; }
                .thinking-dots { display: flex; gap: 4px; }
                .dot { width: 6px; height: 6px; background: var(--vscode-editor-foreground); border-radius: 50%; opacity: 0.4; animation: pulse 1.5s infinite ease-in-out; }
                .dot:nth-child(2) { animation-delay: 0.2s; }
                .dot:nth-child(3) { animation-delay: 0.4s; }
                #loadingText {
                    font-size: 12px; color: var(--vscode-descriptionForeground);
                    font-style: italic; animation: fadeInOut 3s ease-in-out infinite;
                }
                @keyframes pulse {
                    0%, 100% { opacity: 0.4; transform: scale(1); }
                    50% { opacity: 1; transform: scale(1.2); }
                }
                @keyframes fadeInOut {
                    0%, 100% { opacity: 0.5; }
                    50% { opacity: 1; }
                }
            </style>
        </head>
        <body>
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 1px solid var(--vscode-widget-border);">
                <span style="font-weight: bold;">Omni-Agent</span>
                <button id="settingsBtn" style="background: none; border: none; cursor: pointer; color: var(--vscode-descriptionForeground);">Settings</button>
            </div>
            <div id="messages" class="chat-container">
                <div class="onboarding-card">
                    <h3>Welcome to Omni-Agent - Your AI Co-Founder</h3>
                    <div class="mode-item">
                        <span class="mode-icon">L</span>
                        <div>
                            <span class="mode-label">FREE Mode (Ollama):</span>
                            <span class="mode-desc">Download <a href="https://ollama.com" target="_blank">ollama.com</a> then run: <code>ollama pull qwen2.5-coder:3b</code></span>
                        </div>
                    </div>
                    <div class="mode-item">
                        <span class="mode-icon">C</span>
                        <div>
                            <span class="mode-label">Cloud Mode (Gemini):</span>
                            <span class="mode-desc">Tap Settings above - Enter your Gemini API Key for cloud-powered AI</span>
                        </div>
                    </div>
                    <div class="mode-item">
                        <span class="mode-icon">H</span>
                        <div>
                            <span class="mode-label">Hybrid Mode (Recommended):</span>
                            <span class="mode-desc">Use both! Ollama handles local tasks, Gemini handles complex ones - saves your API quota!</span>
                        </div>
                    </div>
                    <div class="try-text">
                        Try: "create a login page using HTML, CSS, JS" - <a href="https://nihu.in" target="_blank">Visit nihu.in</a> for updates
                    </div>
                </div>
            </div>
            <div id="thinking" class="thinking-container">
                <div class="thinking-dots">
                    <div class="dot"></div><div class="dot"></div><div class="dot"></div>
                </div>
                <span id="loadingText">Analyzing your request...</span>
            </div>
            <div class="input-area">
                <textarea id="chatInput" placeholder="Ask anything... e.g. create a dashboard with charts"></textarea>
                <button id="sendBtn">Send</button>
            </div>
            <script>
                const vscode = acquireVsCodeApi();
                const input = document.getElementById('chatInput');
                const sendBtn = document.getElementById('sendBtn');
                const messages = document.getElementById('messages');
                const thinking = document.getElementById('thinking');
                const loadingText = document.getElementById('loadingText');

                const loadingMessages = [
                    "Analyzing your request...",
                    "Thinking deeply about this...",
                    "Generating intelligent code...",
                    "Building components...",
                    "Applying best practices...",
                    "Optimizing for performance...",
                    "Wiring up the logic...",
                    "Polishing the result...",
                    "Almost there, finalizing..."
                ];
                let loadingInterval = null;
                let loadingIndex = 0;

                function startLoadingAnimation() {
                    loadingIndex = 0;
                    loadingText.innerText = loadingMessages[0];
                    thinking.style.display = 'flex';
                    loadingInterval = setInterval(() => {
                        loadingIndex = (loadingIndex + 1) % loadingMessages.length;
                        loadingText.innerText = loadingMessages[loadingIndex];
                    }, 3000);
                }

                function stopLoadingAnimation() {
                    thinking.style.display = 'none';
                    if (loadingInterval) {
                        clearInterval(loadingInterval);
                        loadingInterval = null;
                    }
                }

                async function sendMessage() {
                    const text = input.value.trim();
                    if (!text) return;
                    input.value = '';
                    addMessage(text, 'user');
                    startLoadingAnimation();
                    vscode.postMessage({ command: 'sendChat', text: text });
                }

                window.addEventListener('message', event => {
                    const message = event.data;
                    switch (message.command) {
                        case 'startLoading':
                            startLoadingAnimation();
                            break;
                        case 'receiveResponse':
                            stopLoadingAnimation();
                            if (message.error_type === 'ollama_missing') {
                                renderErrorCard('Brain Not Found', 'Ollama is not running. Please download and start it.', 'Download Ollama', 'openUrl', 'https://ollama.com');
                            } else if (message.error_type === 'model_missing') {
                                renderErrorCard('Model Missing', 'The model qwen2.5-coder:3b is missing.', 'Run Install Command', 'runTerminalCommand', message.command_text);
                            } else {
                                addMessage(message.text, 'ai');
                            }
                            break;
                        case 'showSetupPrompt':
                            renderSetupCard(message.text);
                            break;
                    }
                });

                function renderErrorCard(title, body, btnText, command, payload) {
                    const card = document.createElement('div');
                    card.className = command === 'openUrl' ? 'error-card' : 'warning-card';
                    card.innerHTML = \`
                        <div style="font-weight: bold; margin-bottom: 6px;">\${title}</div>
                        <div style="font-size: 12px; opacity: 0.9; margin-bottom: 10px;">\${body}</div>
                        <button class="btn-install" id="actionBtn">\${btnText}</button>
                    \`;
                    messages.appendChild(card);
                    messages.scrollTop = messages.scrollHeight;

                    const btn = card.querySelector('#actionBtn');
                    btn.onclick = () => {
                        btn.disabled = true;
                        btn.innerText = (command === 'openUrl') ? 'Opening...' : 'Installing... Check Terminal!';
                        const msg = (command === 'openUrl') ? { command, url: payload } : { command, text: payload };
                        vscode.postMessage(msg);
                    };
                }

                function renderSetupCard(reason) {
                    const card = document.createElement('div');
                    card.className = 'setup-card';
                    card.innerHTML = \`
                        <h3>Omni Cloud Setup</h3>
                        <p>\${reason}</p>
                        <div class="setup-btns">
                            <button id="cardSetupBtn">Setup Gemini Key</button>
                            <button id="cardLocalBtn" class="secondary">Use Local Mode</button>

                        </div>
                    \`;
                    messages.appendChild(card);
                    messages.scrollTop = messages.scrollHeight;
                    card.querySelector('#cardSetupBtn').onclick = () => vscode.postMessage({ command: 'openSettings' });
                    card.querySelector('#cardLocalBtn').onclick = () => card.remove();                }

                sendBtn.addEventListener('click', sendMessage);
                document.getElementById('settingsBtn').addEventListener('click', () => {
                    vscode.postMessage({ command: 'openSettings' });
                });
                input.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendMessage();
                    }
                });
                function addMessage(text, sender) {
                    const div = document.createElement('div');
                    div.className = 'message ' + sender;
                    div.innerText = text;
                    messages.appendChild(div);
                    messages.scrollTop = messages.scrollHeight;
                }
            </script>
        </body>
        </html>`;
	}
}
function deactivate() {
	if (pythonProcess) {
		pythonProcess.kill();
	}
}
//# sourceMappingURL=extension.js.map
