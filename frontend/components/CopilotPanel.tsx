'use client';
import React, { useState, useEffect } from 'react';
import { useCopilot } from '../hooks/useCopilot';
import StatusIndicator from './copilot/StatusIndicator';
import IntentCard from './copilot/IntentCard';
import ExecutionSummaryCard from './copilot/ExecutionSummaryCard';
import InsightsFeed from './copilot/InsightsFeed';
import ExplainabilityFeed from './copilot/ExplainabilityFeed';
import TemplatePanel from './copilot/TemplatePanel';
import AnalyticsPanel from './copilot/AnalyticsPanel';

export default function CopilotPanel() {
    const copilot = useCopilot();
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [insightsFetched, setInsightsFetched] = useState(false);

    // Fetch insights on mount (one-shot read-only)
    useEffect(() => {
        const fetchInsights = async () => {
            try {
                const res = await fetch('http://localhost:8000/api/insights');
                if (res.ok) {
                    const data = await res.json();
                    if (data.insights && data.insights.length > 0) {
                        const { default: store } = await import('../stores/copilotStore');
                        store.pushInsights(data.insights);
                    }
                }
            } catch {
                // Insights service offline — gracefully hidden
            }
            setInsightsFetched(true);
        };
        fetchInsights();
    }, []);

    return (
        <div id="copilot-panel" style={{
            width: isCollapsed ? '48px' : '280px',
            minHeight: '200px',
            background: 'linear-gradient(180deg, rgba(15,23,42,0.97), rgba(20,27,45,0.95))',
            borderRadius: '14px',
            border: '1px solid rgba(99,102,241,0.2)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
            transition: 'width 0.3s ease, opacity 0.3s ease',
            overflow: 'hidden',
            fontFamily: "'Inter', sans-serif",
            position: 'fixed',
            top: '24px',
            right: '24px',
            zIndex: 45,
        }}>
            {/* Header */}
            <div
                onClick={() => setIsCollapsed(!isCollapsed)}
                style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: isCollapsed ? '12px 14px' : '12px 16px',
                    cursor: 'pointer', userSelect: 'none',
                    borderBottom: isCollapsed ? 'none' : '1px solid rgba(99,102,241,0.12)',
                }}
            >
                {isCollapsed ? (
                    <span style={{ fontSize: '16px' }}>🤖</span>
                ) : (
                    <>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{ fontSize: '14px' }}>🤖</span>
                            <span style={{ fontSize: '13px', fontWeight: 700, color: '#e2e8f0', letterSpacing: '0.3px' }}>
                                Copilot
                            </span>
                            <HealthScoreBadge />
                        </div>
                        <span style={{ fontSize: '11px', color: '#475569', transition: 'transform 0.2s' }}>
                            {isCollapsed ? '◀' : '▶'}
                        </span>
                    </>
                )}
            </div>

            {/* Body — only when expanded */}
            {!isCollapsed && (
                <div style={{ padding: '8px 12px 14px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {/* Section 1: System Status */}
                    <div>
                        <SectionLabel text="System Status" />
                        <StatusIndicator status={copilot.status} />
                    </div>

                    {/* Section 2: Current Intent */}
                    <div>
                        <SectionLabel text="Detected Intent" />
                        <IntentCard intent={copilot.intent} />
                    </div>

                    {/* Section 3: Execution Summary (only when active) */}
                    {copilot.execution && (
                        <div>
                            <SectionLabel text="Execution" />
                            <ExecutionSummaryCard execution={copilot.execution} />
                        </div>
                    )}

                    {/* Section 4: Recent Insights */}
                    <div>
                        <SectionLabel text="Insights" />
                        <InsightsFeed insights={copilot.insights} />
                    </div>

                    {/* Section 5: Why did this happen? (Explainability) */}
                    <div>
                        <SectionLabel text="System Reasoning" />
                        <ExplainabilityFeed explanations={copilot.explanations} />
                    </div>

                    {/* Section 6: Workflow Templates */}
                    <div>
                        <SectionLabel text="Available Workflows" />
                        <TemplatePanel />
                    </div>

                    {/* Section 7: System Analytics */}
                    <div>
                        <SectionLabel text="Usage & Health" />
                        <AnalyticsPanel />
                    </div>
                </div>
            )}
        </div>
    );
}

function SectionLabel({ text }: { text: string }) {
    return (
        <p style={{
            fontSize: '9px', fontWeight: 700, color: '#475569',
            textTransform: 'uppercase', letterSpacing: '1px',
            margin: '0 0 4px 2px',
        }}>
            {text}
        </p>
    );
}

function HealthScoreBadge() {
    const [score, setScore] = useState<number | null>(null);

    useEffect(() => {
        fetch('http://localhost:8000/api/analytics/summary')
            .then(res => res.json())
            .then(data => setScore(data.health_score))
            .catch(() => { });
    }, []);

    if (score === null) return null;

    return (
        <div style={{
            fontSize: '9px', fontWeight: 900,
            padding: '1px 5px', borderRadius: '4px',
            marginLeft: 'auto', marginRight: '8px',
            background: score > 0.7 ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.2)',
            color: score > 0.7 ? '#4ade80' : '#f87171',
            border: `1px solid ${score > 0.7 ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}`,
            whiteSpace: 'nowrap'
        }}>
            {Math.round(score * 100)} HPI
        </div>
    );
}
