'use client';
import React, { useState } from 'react';
import { ExplainabilityEvent } from '../../stores/copilotStore';
import FeedbackButtons from './FeedbackButtons';

interface ExplainabilityFeedProps {
    explanations: ExplainabilityEvent[];
}

const SOURCE_COLORS: Record<string, string> = {
    router: '#A855F7',      // Purple
    planner: '#3B82F6',     // Blue
    insights: '#22C55E',    // Green
    orchestrator: '#F59E0B' // Amber
};

export default function ExplainabilityFeed({ explanations }: ExplainabilityFeedProps) {
    const [isExpanded, setIsExpanded] = useState(false);

    if (!explanations || explanations.length === 0) {
        return (
            <div style={{
                padding: '8px 14px', borderRadius: '8px',
                background: 'rgba(30,41,59,0.4)', color: '#475569',
                fontSize: '11px', fontStyle: 'italic',
            }}>
                No explanations generated yet.
            </div>
        );
    }

    const displayCount = isExpanded ? explanations.length : 3;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {explanations.slice(0, displayCount).map((event) => {
                const color = SOURCE_COLORS[event.source] || '#64748B';
                const timeStr = new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

                return (
                    <div key={event.id} style={{
                        padding: '8px 10px', borderRadius: '6px',
                        background: 'rgba(30,41,59,0.35)',
                        borderLeft: `2px solid ${color}`,
                        display: 'flex', flexDirection: 'column', gap: '4px'
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{
                                fontSize: '9px', fontWeight: 600, color: color,
                                textTransform: 'uppercase', letterSpacing: '0.5px'
                            }}>
                                {event.source}
                            </span>
                            <span style={{ fontSize: '9px', color: '#64748B' }}>
                                {timeStr}
                            </span>
                        </div>
                        <span style={{ fontSize: '11px', color: '#CBD5E1', lineHeight: 1.4, marginBottom: '4px' }}>
                            {event.summary}
                        </span>

                        {/* Phase 7 Sprint 3: Feedback Buttons */}
                        <div style={{ display: 'flex', justifyContent: 'flex-start', marginTop: '2px' }}>
                            <FeedbackButtons
                                eventId={event.id}
                                module={event.source as any}
                                context={{ summary: event.summary, reasonCode: event.reasonCode }}
                            />
                        </div>
                    </div>
                );
            })}

            {explanations.length > 3 && (
                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    style={{
                        background: 'transparent', border: 'none',
                        color: '#6366F1', fontSize: '10px', fontWeight: 600,
                        cursor: 'pointer', padding: '4px 0', textAlign: 'center',
                        marginTop: '2px', textTransform: 'uppercase'
                    }}
                >
                    {isExpanded ? 'Show less' : `Show ${explanations.length - 3} more`}
                </button>
            )}
        </div>
    );
}
