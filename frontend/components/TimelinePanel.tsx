'use client';
import React, { useState } from 'react';
import TimelineGraph from './TimelineGraph';
import { useDagEvents } from '../hooks/useDagEvents';

export default function TimelinePanel() {
    const dagState = useDagEvents();
    const [isCollapsed, setIsCollapsed] = useState(false);

    // Auto-hide when no DAG is active
    if (!dagState.isActive && dagState.nodes.length === 0) return null;

    const progressPercent = Math.round(dagState.progress * 100);

    return (
        <div
            style={{
                position: 'sticky',
                top: '12px',
                zIndex: 40,
                width: '100%',
                maxWidth: '320px',
                background: 'linear-gradient(145deg, rgba(15,23,42,0.95), rgba(30,41,59,0.92))',
                borderRadius: '12px',
                border: '1px solid rgba(99,102,241,0.25)',
                boxShadow: '0 4px 24px rgba(0,0,0,0.35)',
                overflow: 'hidden',
                transition: 'opacity 0.4s ease, transform 0.3s ease',
                opacity: dagState.isActive ? 1 : 0.5,
                fontFamily: "'Inter', sans-serif",
            }}
        >
            {/* Header */}
            <div
                onClick={() => setIsCollapsed(!isCollapsed)}
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 14px',
                    cursor: 'pointer',
                    borderBottom: isCollapsed ? 'none' : '1px solid rgba(99,102,241,0.15)',
                    userSelect: 'none',
                }}
            >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '14px' }}>🧭</span>
                    <span style={{ fontSize: '13px', fontWeight: 600, color: '#e2e8f0' }}>
                        Execution Timeline
                    </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '11px', color: '#94a3b8' }}>
                        {progressPercent}%
                    </span>
                    <span style={{ fontSize: '12px', color: '#64748b', transition: 'transform 0.2s' }}>
                        {isCollapsed ? '▶' : '▼'}
                    </span>
                </div>
            </div>

            {/* Progress Bar */}
            <div style={{ width: '100%', height: '3px', background: '#1e293b' }}>
                <div
                    style={{
                        height: '100%',
                        width: `${progressPercent}%`,
                        background: 'linear-gradient(90deg, #6366f1, #22c55e)',
                        transition: 'width 0.4s ease',
                        borderRadius: '0 2px 2px 0',
                    }}
                />
            </div>

            {/* Collapsible Body */}
            {!isCollapsed && (
                <div style={{ padding: '8px 6px 12px 6px', maxHeight: '280px', overflowY: 'auto' }}>
                    <TimelineGraph nodes={dagState.nodes} currentNode={dagState.currentNode} />
                </div>
            )}
        </div>
    );
}
