"use client";

import React, { useEffect, useRef, useState, useCallback } from 'react';
import DiffViewerPanel from './DiffViewerPanel';
import TimelinePanel from './TimelinePanel';
import CopilotPanel from './CopilotPanel';
import { patchService, PatchSession } from '../services/patchService';
import { dispatchDagUpdate } from '../hooks/useDagEvents';
import copilotStore from '../stores/copilotStore';

type LogMessage = {
  type: 'info' | 'transcription' | 'agent_response' | 'error';
  text: string;
  timestamp: string;
};

// Typewriter Component removed in favor of real-time streaming

export default function Dashboard() {
  const [logs, setLogs] = useState<LogMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [textInput, setTextInput] = useState('');
  const [isAgentBusy, setIsAgentBusy] = useState(false);
  const [activeSessions, setActiveSessions] = useState<PatchSession[]>([]);

  const openSessionInChat = (session: PatchSession) => {
    addLog('agent_response', `Restoring pending patch from queue...\nSession ID: ${session.session_id}`);
    setActiveSessions(prev => prev.filter(s => s.session_id !== session.session_id));
  };

  const socketRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const screenStreamRef = useRef<MediaStream | null>(null);
  const screenIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const tokenBufferRef = useRef<string>("");

  const addLog = (type: LogMessage['type'], text: string) => {
    setLogs(prev => [...prev, { type, text, timestamp: new Date().toLocaleTimeString() }]);
  };

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: NodeJS.Timeout | null = null;

    const loadSessions = async () => {
      try {
        const sessions = await patchService.fetchActiveSessions();
        setActiveSessions(sessions);
      } catch (err) {
        console.error("Failed to load active sessions", err);
      }
    };
    loadSessions();

    // Flush buffer every 100ms to avoid render thrashing
    const flushInterval = setInterval(() => {
      if (tokenBufferRef.current) {
        const textToFlush = tokenBufferRef.current;
        tokenBufferRef.current = "";

        setLogs(prev => {
          const newLogs = [...prev];
          if (newLogs.length > 0) {
            const lastLog = newLogs[newLogs.length - 1];
            if (lastLog.type === 'agent_response') {
              newLogs[newLogs.length - 1] = {
                ...lastLog,
                text: lastLog.text + textToFlush
              };
              return newLogs;
            }
          }
          // Fallback if no active log
          return [...prev, { type: 'agent_response', text: textToFlush, timestamp: new Date().toLocaleTimeString() }];
        });
      }
    }, 100);

    // Function to connect to WebSocket
    const connect = () => {
      ws = new WebSocket('ws://localhost:8000/ws/omni');
      socketRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        addLog('info', 'Connected to Omni-Agent Backend');
        if (reconnectTimer) clearTimeout(reconnectTimer);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'transcription') {
            addLog('transcription', `User: ${data.text}`);
          } else if (data.type === 'agent_response_start') {
            setIsAgentBusy(true);
            tokenBufferRef.current = "";
            addLog('agent_response', '');
          } else if (data.type === 'agent_token') {
            tokenBufferRef.current += data.text;
          } else if (data.type === 'agent_response_end') {
            setIsAgentBusy(false);
          } else if (data.type === 'dag_update') {
            // Phase 6: Dispatch DAG execution events to Timeline UI
            dispatchDagUpdate(data);
            // Phase 7: Dispatch to Copilot Store
            copilotStore.pushDagUpdate(data);
          } else if (data.type === 'copilot_event') {
            // Phase 7: Handle generic copilot events
            if (data.source === 'router' && data.payload.type === 'intent') {
              copilotStore.pushIntent(data.payload.label, data.payload.confidence, data.payload.explanation);
            } else if (data.source === 'insights') {
              copilotStore.pushInsights(data.payload.insights);
            } else if (data.payload.type === 'explainability_event') {
              copilotStore.pushExplainability(data.payload);
            }
          }
        } catch (e) {
          console.error("Failed to parse message", e);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        addLog('error', 'Disconnected. Retrying in 3s...');
        if (!reconnectTimer) {
          reconnectTimer = setTimeout(connect, 3000);
        }
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        addLog('error', 'WebSocket error occurred');
        ws?.close();
      };
    };

    // Initial connection
    connect();

    return () => {
      clearInterval(flushInterval);
      if (ws) {
        ws.onclose = null;
        ws.close();
      }
      if (reconnectTimer) clearTimeout(reconnectTimer);

      if (mediaRecorderRef.current) mediaRecorderRef.current.stop();
      if (screenStreamRef.current) screenStreamRef.current.getTracks().forEach(track => track.stop());
      if (screenIntervalRef.current) clearInterval(screenIntervalRef.current);
    };
  }, []);

  const startAudio = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && socketRef.current?.readyState === WebSocket.OPEN) {
          socketRef.current.send(event.data);
        }
      };

      mediaRecorder.start(); // No timeslice: record until stopped
      setIsRecording(true);
      addLog('info', 'Microphone recording started (Click Stop to send)');
    } catch (err) {
      console.error("Error accessing microphone:", err);
      addLog('error', 'Failed to access microphone');
    }
  };

  const stopAudio = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
      addLog('info', 'Microphone recording stopped');
    }
  };

  const startScreenShare = async () => {
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({ video: true });
      screenStreamRef.current = stream;
      setIsScreenSharing(true);
      addLog('info', 'Screen sharing started');

      const videoTrack = stream.getVideoTracks()[0];
      // ImageCapture logic removed/simplified as it caused TS issues previously,
      // focusing on Canvas based approach which is more reliable across browsers.

      const video = document.createElement('video');
      video.srcObject = stream;
      video.play();

      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');

      screenIntervalRef.current = setInterval(() => {
        if (socketRef.current?.readyState === WebSocket.OPEN && ctx) {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          const base64Image = canvas.toDataURL('image/jpeg', 0.5); // Quality 0.5

          socketRef.current.send(JSON.stringify({
            type: "screen_frame",
            image: base64Image
          }));
        }
      }, 1000); // 1 FPS

      videoTrack.onended = () => {
        stopScreenShare();
      };

    } catch (err) {
      console.error("Error accessing screen:", err);
      addLog('error', 'Failed to share screen');
    }
  };

  const stopScreenShare = () => {
    if (screenStreamRef.current) {
      screenStreamRef.current.getTracks().forEach(track => track.stop());
      setIsScreenSharing(false);
      if (screenIntervalRef.current) clearInterval(screenIntervalRef.current);
      addLog('info', 'Screen sharing stopped');
    }
  };

  const sendTextInput = () => {
    const text = textInput.trim();
    if (!text || !socketRef.current || socketRef.current.readyState !== WebSocket.OPEN || isAgentBusy) return;
    socketRef.current.send(JSON.stringify({ type: 'text_input', text }));
    setTextInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendTextInput();
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white font-sans p-8">
      <CopilotPanel />
      <header className="mb-8 flex justify-between items-center bg-gray-800 p-4 rounded-xl shadow-lg border border-gray-700">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            Omni-Agent Studio
          </h1>
          <p className="text-gray-400 text-sm mt-1">Autonomous Digital Worker Platform</p>
        </div>
        <div className={`px-4 py-2 rounded-full text-sm font-semibold flex items-center gap-2 ${isConnected ? 'bg-green-500/20 text-green-400 border border-green-500/50' : 'bg-red-500/20 text-red-400 border border-red-500/50'}`}>
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></div>
          {isConnected ? 'System Online' : 'System Offline'}
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Controls Panel */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-gray-800 p-6 rounded-2xl shadow-xl border border-gray-700">
            <h2 className="text-xl font-semibold mb-4 text-gray-200">Sensor Controls</h2>
            <div className="space-y-4">
              <button
                onClick={isRecording ? stopAudio : startAudio}
                className={`w-full py-3 px-4 rounded-lg font-medium transition-all duration-200 flex items-center justify-center gap-2 ${isRecording
                  ? 'bg-red-500/20 text-red-300 border border-red-500/50 hover:bg-red-500/30'
                  : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20'
                  }`}
              >
                {isRecording ? (
                  <>
                    <span className="animate-pulse">●</span> Stop Voice
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path></svg>
                    Enable Voice (Mic)
                  </>
                )}
              </button>

              <button
                onClick={isScreenSharing ? stopScreenShare : startScreenShare}
                className={`w-full py-3 px-4 rounded-lg font-medium transition-all duration-200 flex items-center justify-center gap-2 ${isScreenSharing
                  ? 'bg-red-500/20 text-red-300 border border-red-500/50 hover:bg-red-500/30'
                  : 'bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-500/20'
                  }`}
              >
                {isScreenSharing ? (
                  <>
                    <span className="animate-pulse">●</span> Stop Vision
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
                    Enable Vision (Screen)
                  </>
                )}
              </button>
            </div>

            {/* Text Input */}
            <div className="mt-4 pt-4 border-t border-gray-700">
              <label className="text-sm text-gray-400 mb-2 block">Chat with Agent</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={isAgentBusy ? 'Agent is thinking...' : 'Type a command...'}
                  disabled={!isConnected || isAgentBusy}
                  className="flex-1 bg-gray-700 text-white rounded-lg px-4 py-2 text-sm border border-gray-600 focus:border-blue-500 focus:outline-none placeholder-gray-500 disabled:opacity-50"
                />
                <button
                  onClick={sendTextInput}
                  disabled={!isConnected || isAgentBusy || !textInput.trim()}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-all disabled:opacity-30 disabled:cursor-not-allowed shadow-lg shadow-blue-500/20"
                >
                  {isAgentBusy ? (
                    <span className="animate-spin inline-block">⏳</span>
                  ) : (
                    'Send'
                  )}
                </button>
              </div>
            </div>
          </div>

          <div className="bg-gray-800 p-6 rounded-2xl shadow-xl border border-gray-700">
            <h2 className="text-xl font-semibold mb-2 text-gray-200">System Status</h2>
            <div className="text-sm text-gray-400 space-y-2">
              <div className="flex justify-between">
                <span>Backend</span>
                <span className={isConnected ? "text-green-400" : "text-red-400"}>{isConnected ? "Connected" : "Disconnected"}</span>
              </div>
              <div className="flex justify-between">
                <span>Voice Module</span>
                <span className={isRecording ? "text-blue-400" : "text-gray-600"}>{isRecording ? "Active" : "Idle"}</span>
              </div>
              <div className="flex justify-between">
                <span>Vision Module</span>
                <span className={isScreenSharing ? "text-purple-400" : "text-gray-600"}>{isScreenSharing ? "Active" : "Idle"}</span>
              </div>
            </div>
          </div>

          {/* Phase 6: Execution Timeline UI */}
          <TimelinePanel />

          {/* Pending Patches Queue (Sprint 3) */}
          {activeSessions.length > 0 && (
            <div className="bg-gray-800 p-6 rounded-2xl shadow-xl border border-blue-500/30">
              <h2 className="text-xl font-semibold mb-3 text-gray-200 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></span>
                Action Required
              </h2>
              <div className="space-y-3 max-h-48 overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-gray-600">
                {activeSessions.map((session, idx) => (
                  <div key={idx} className="bg-gray-700/50 p-3 rounded-lg border border-gray-600 hover:border-blue-500/50 transition-colors cursor-pointer group" onClick={() => openSessionInChat(session)}>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm font-semibold text-gray-200 truncate pr-2">
                        📄 {session.file_path.split(/[\\/]/).pop()}
                      </span>
                      <span className="text-xs bg-yellow-500/20 text-yellow-500 px-2 py-0.5 rounded-full font-medium">
                        {session.status}
                      </span>
                    </div>
                    <div className="flex justify-between text-xs text-gray-400 items-center mt-2">
                      <span>{Math.max(0, Math.round((Date.now() - session.created_at * 1000) / 60000))} min ago</span>
                      <span className="text-blue-400 font-semibold opacity-0 group-hover:opacity-100 transition-opacity">Review ▸</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Logs Panel */}
        <div className="lg:col-span-2 bg-black/40 p-6 rounded-2xl border border-gray-700/50 backdrop-blur-sm h-[600px] flex flex-col">
          <h2 className="text-xl font-semibold mb-4 text-gray-200 flex items-center gap-2">
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg>
            Agent Activity Log
          </h2>
          <div className="flex-1 overflow-y-auto space-y-4 pr-2 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
            {logs.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-gray-600">
                <p>No activity yet.</p>
                <p className="text-sm">Start voice or vision to interact.</p>
              </div>
            )}

            {logs.map((log, index) => {
              const sessionIdMatch = log.type === 'agent_response' ? log.text.match(/Session ID: ([a-f0-9\-]+)/) : null;
              const sessionId = sessionIdMatch ? sessionIdMatch[1] : null;

              return (
                <div
                  key={index}
                  className={`p-4 rounded-xl border ${log.type === 'agent_response' ? 'bg-blue-900/20 border-blue-500/30 ml-8' :
                    log.type === 'transcription' ? 'bg-gray-800/50 border-gray-700 mr-8' :
                      log.type === 'error' ? 'bg-red-900/20 border-red-500/30' :
                        'bg-gray-800/30 border-gray-700/50 text-gray-400 text-sm text-center'
                    }`}
                >
                  <div className="flex justify-between items-start mb-1">
                    <span className={`text-xs font-bold uppercase tracking-wider ${log.type === 'agent_response' ? 'text-blue-400' :
                      log.type === 'transcription' ? 'text-green-400' :
                        log.type === 'error' ? 'text-red-400' : 'text-gray-500'
                      }`}>
                      {log.type === 'agent_response' ? 'Agent' : log.type === 'transcription' ? 'User' : log.type.toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-500">{log.timestamp}</span>
                  </div>
                  {log.type === 'agent_response' ? (
                    <>
                      <p className="text-gray-200 whitespace-pre-wrap font-mono text-sm">
                        {sessionId ? log.text.replace(sessionIdMatch![0], '') : log.text}
                        <span className="animate-pulse inline-block w-2 h-4 bg-blue-400 ml-1"></span>
                      </p>
                      {sessionId && (
                        <div className="mt-3">
                          <DiffViewerPanel sessionId={sessionId} />
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="group relative">
                      <p className="text-gray-200 whitespace-pre-wrap">{log.text}</p>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div >
  );
}
