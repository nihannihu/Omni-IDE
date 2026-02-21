'use client';
import React from 'react';
import { CopilotExecution } from '../../stores/copilotStore';

interface ExecutionSummaryCardProps {
    execution: CopilotExecution | null;
}

export default function ExecutionSummaryCard({ execution }: ExecutionSummaryCardProps) {
    if (!execution) return null;

    const progressPct = Math.round(execution.progress * 100);

    return (
        <div style={{
            padding: '10px 14px', borderRadius: '8px',
            background: 'rgba(30,41,59,0.5)',
            border: `1px solid ${execution.isActive ? 'rgba(59,130,246,0.3)' : 'rgba(34,197,94,0.2)'}`,
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <span style={{ fontSize: '12px', fontWeight: 600, color: '#e2e8f0' }}>
                    ⚙️ {execution.templateContext ? `Workflow: ${execution.templateContext.template_name}` : execution.graphName}
                </span>
                <span style={{
                    fontSize: '10px', fontWeight: 700,
                    color: execution.isActive ? '#3b82f6' : '#22c55e',
                }}>
                    {execution.completedNodes}/{execution.totalNodes}
                </span>
            </div>

            {/* Progress Bar */}
            <div style={{ width: '100%', height: '4px', borderRadius: '2px', background: '#1e293b', marginBottom: '6px' }}>
                <div style={{
                    height: '100%', width: `${progressPct}%`,
                    background: execution.isActive
                        ? 'linear-gradient(90deg, #6366f1, #3b82f6)'
                        : 'linear-gradient(90deg, #22c55e, #16a34a)',
                    borderRadius: '2px',
                    transition: 'width 0.4s ease',
                }} />
            </div>

            {execution.currentNode && execution.isActive && (
                <p style={{ fontSize: '11px', color: '#94a3b8', margin: 0 }}>
                    🔵 Running: <span style={{ color: '#cbd5e1', fontWeight: 500 }}>
                        {execution.currentNode.replace(/_/g, ' ')}
                    </span>
                </p>
            )}

            {!execution.isActive && (
                <p style={{ fontSize: '11px', color: '#22c55e', margin: 0 }}>
                    ✅ Execution complete
                </p>
            )}
        </div>
    );
}
