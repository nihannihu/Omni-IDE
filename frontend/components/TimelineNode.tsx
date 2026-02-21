'use client';
import React from 'react';

interface TimelineNodeProps {
    id: string;
    status: string;
    isCurrent: boolean;
}

const STATUS_CONFIG: Record<string, { icon: string; color: string; bg: string; label: string }> = {
    PENDING: { icon: '🟡', color: '#a3a3a3', bg: 'rgba(163,163,163,0.1)', label: 'Pending' },
    RUNNING: { icon: '🔵', color: '#3b82f6', bg: 'rgba(59,130,246,0.15)', label: 'Running' },
    COMPLETED: { icon: '🟢', color: '#22c55e', bg: 'rgba(34,197,94,0.12)', label: 'Completed' },
    FAILED: { icon: '🔴', color: '#ef4444', bg: 'rgba(239,68,68,0.12)', label: 'Failed' },
    UNKNOWN: { icon: '⚪', color: '#6b7280', bg: 'rgba(107,114,128,0.1)', label: 'Unknown' },
};

export default function TimelineNode({ id, status, isCurrent }: TimelineNodeProps) {
    const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.UNKNOWN;

    return (
        <div
            style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '8px 14px',
                borderRadius: '8px',
                background: isCurrent ? cfg.bg : 'transparent',
                borderLeft: isCurrent ? `3px solid ${cfg.color}` : '3px solid transparent',
                transition: 'all 0.25s ease',
                fontFamily: "'Inter', sans-serif",
            }}
        >
            <span style={{ fontSize: '14px' }}>{cfg.icon}</span>
            <span
                style={{
                    flex: 1,
                    fontSize: '13px',
                    fontWeight: isCurrent ? 600 : 400,
                    color: isCurrent ? '#e2e8f0' : '#94a3b8',
                    textTransform: 'capitalize',
                }}
            >
                {id.replace(/_/g, ' ')}
            </span>
            <span
                style={{
                    fontSize: '10px',
                    fontWeight: 600,
                    color: cfg.color,
                    padding: '2px 8px',
                    borderRadius: '10px',
                    background: cfg.bg,
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                }}
            >
                {cfg.label}
            </span>
        </div>
    );
}
