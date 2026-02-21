'use client';
import React from 'react';
import { CopilotStatus } from '../../stores/copilotStore';

interface StatusIndicatorProps {
    status: CopilotStatus;
}

const STATUS_MAP: Record<CopilotStatus, { icon: string; label: string; color: string; pulse: boolean }> = {
    idle: { icon: '💤', label: 'Idle', color: '#64748b', pulse: false },
    planning: { icon: '🧠', label: 'Planning', color: '#a78bfa', pulse: true },
    executing: { icon: '⚡', label: 'Executing', color: '#3b82f6', pulse: true },
    waiting: { icon: '⏳', label: 'Waiting', color: '#f59e0b', pulse: true },
};

export default function StatusIndicator({ status }: StatusIndicatorProps) {
    const cfg = STATUS_MAP[status] || STATUS_MAP.idle;

    return (
        <div style={{
            display: 'flex', alignItems: 'center', gap: '8px',
            padding: '8px 12px', borderRadius: '8px',
            background: 'rgba(30,41,59,0.6)',
        }}>
            <span style={{
                fontSize: '12px',
                animation: cfg.pulse ? 'pulse 1.5s ease-in-out infinite' : 'none',
            }}>
                {cfg.icon}
            </span>
            <span style={{
                fontSize: '11px', fontWeight: 600, color: cfg.color,
                textTransform: 'uppercase', letterSpacing: '0.8px',
            }}>
                {cfg.label}
            </span>
            {cfg.pulse && (
                <span style={{
                    width: '6px', height: '6px', borderRadius: '50%',
                    background: cfg.color, boxShadow: `0 0 6px ${cfg.color}`,
                    animation: 'pulse 1.5s ease-in-out infinite',
                }} />
            )}
        </div>
    );
}
