'use client';
import React from 'react';
import { CopilotIntent } from '../../stores/copilotStore';
import FeedbackButtons from './FeedbackButtons';

interface IntentCardProps {
    intent: CopilotIntent | null;
}

export default function IntentCard({ intent }: IntentCardProps) {
    if (!intent) {
        return (
            <div style={{
                padding: '10px 14px', borderRadius: '8px',
                background: 'rgba(30,41,59,0.4)', color: '#475569',
                fontSize: '12px', fontStyle: 'italic',
            }}>
                Waiting for user input…
            </div>
        );
    }

    const confidencePct = Math.round(intent.confidence * 100);
    const barColor = confidencePct >= 80 ? '#22c55e' : confidencePct >= 50 ? '#f59e0b' : '#ef4444';

    return (
        <div style={{
            padding: '10px 14px', borderRadius: '8px',
            background: 'rgba(30,41,59,0.5)',
            border: '1px solid rgba(99,102,241,0.15)',
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <span style={{ fontSize: '13px', fontWeight: 600, color: '#e2e8f0' }}>
                    🎯 {intent.label}
                </span>
                <span style={{
                    fontSize: '10px', fontWeight: 700, color: barColor,
                    padding: '2px 8px', borderRadius: '10px',
                    background: `${barColor}18`,
                }}>
                    {confidencePct}%
                </span>
            </div>
            {/* Confidence Bar */}
            <div style={{ width: '100%', height: '3px', borderRadius: '2px', background: '#1e293b', marginBottom: '6px' }}>
                <div style={{
                    height: '100%', width: `${confidencePct}%`,
                    background: barColor, borderRadius: '2px',
                    transition: 'width 0.3s ease',
                }} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <p style={{ fontSize: '11px', color: '#94a3b8', margin: 0, lineHeight: 1.4, flex: 1 }}>
                    {intent.explanation}
                </p>

                {/* Phase 7 Sprint 3: Feedback Buttons */}
                <div style={{ marginLeft: '8px' }}>
                    <FeedbackButtons
                        eventId={`intent-${intent.timestamp}`}
                        module="router"
                        context={{ intent: intent.label, confidence: intent.confidence }}
                    />
                </div>
            </div>
        </div>
    );
}
