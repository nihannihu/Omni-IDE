'use client';
import React from 'react';
import { CopilotInsight } from '../../stores/copilotStore';
import FeedbackButtons from './FeedbackButtons';

interface InsightsFeedProps {
    insights: CopilotInsight[];
}

const SEVERITY_CFG: Record<string, { icon: string; color: string }> = {
    high: { icon: '🔴', color: '#ef4444' },
    medium: { icon: '🟡', color: '#f59e0b' },
    low: { icon: '🔵', color: '#3b82f6' },
};

export default function InsightsFeed({ insights }: InsightsFeedProps) {
    if (!insights || insights.length === 0) {
        return (
            <div style={{
                padding: '8px 14px', borderRadius: '8px',
                background: 'rgba(30,41,59,0.4)', color: '#475569',
                fontSize: '11px', fontStyle: 'italic',
            }}>
                No insights detected yet.
            </div>
        );
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {insights.map((ins) => {
                const cfg = SEVERITY_CFG[ins.severity] || SEVERITY_CFG.low;
                return (
                    <div key={ins.id} style={{
                        display: 'flex', alignItems: 'center', gap: '8px',
                        padding: '6px 10px', borderRadius: '6px',
                        background: 'rgba(30,41,59,0.35)',
                        transition: 'background 0.2s ease',
                    }}>
                        <div style={{ display: 'flex', flex: 1, alignItems: 'center', gap: '8px' }}>
                            <span style={{ fontSize: '11px' }}>{cfg.icon}</span>
                            <span style={{
                                flex: 1, fontSize: '11px', color: '#cbd5e1',
                                whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                            }}>
                                {ins.title}
                            </span>
                            <span style={{
                                fontSize: '9px', color: cfg.color, fontWeight: 600,
                                textTransform: 'uppercase', flexShrink: 0,
                                marginRight: '4px'
                            }}>
                                {ins.severity}
                            </span>
                        </div>
                        <FeedbackButtons eventId={ins.id} module="insight" context={{ title: ins.title }} />
                    </div>
                );
            })}
        </div>
    );
}
