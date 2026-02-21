'use client';
import React, { useState, useEffect } from 'react';

interface UsageSummary {
    health_score: number;
    workflow_success_rate: number;
    template_adoption_rate: number;
    patch_acceptance_rate: number;
    insight_acceptance_rate: number;
    total_events: number;
}

interface FeatureAdoption {
    most_used_template: string;
    template_breakdown: Record<string, number>;
}

export default function AnalyticsPanel() {
    const [summary, setSummary] = useState<UsageSummary | null>(null);
    const [adoption, setAdoption] = useState<FeatureAdoption | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const fetchData = async () => {
        setIsLoading(true);
        try {
            const [sRes, aRes] = await Promise.all([
                fetch('http://localhost:8000/api/analytics/summary'),
                fetch('http://localhost:8000/api/analytics/workflows')
            ]);
            setSummary(await sRes.json());
            setAdoption(await aRes.json());
        } catch (err) {
            console.error("Failed to fetch analytics:", err);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleReset = async () => {
        if (!confirm("Are you sure you want to clear all analytics data? This is local-only and irreversible.")) return;
        try {
            await fetch('http://localhost:8000/api/analytics/reset', { method: 'DELETE' });
            fetchData();
        } catch (err) {
            console.error("Failed to reset analytics:", err);
        }
    };

    if (isLoading) return <div style={{ fontSize: '11px', color: '#94a3b8' }}>Analyzing usage data...</div>;

    if (!summary) return null;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {/* System Health Score */}
            <div style={{
                padding: '12px', borderRadius: '8px',
                background: 'rgba(30,41,59,0.5)', border: '1px solid rgba(255,255,255,0.1)',
                display: 'flex', flexDirection: 'column', gap: '8px'
            }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8' }}>System Health</span>
                    <span style={{
                        fontSize: '18px', fontWeight: 800,
                        color: summary.health_score > 0.7 ? '#22c55e' : (summary.health_score > 0.4 ? '#eab308' : '#ef4444')
                    }}>
                        {(summary.health_score * 100).toFixed(0)}%
                    </span>
                </div>

                {/* Micro-bars for sub-metrics */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <MetricBar label="Workflow Success" value={summary.workflow_success_rate} color="#3b82f6" />
                    <MetricBar label="Template Adoption" value={summary.template_adoption_rate} color="#a855f7" />
                    <MetricBar label="Patch Acceptance" value={summary.patch_acceptance_rate} color="#22c55e" />
                    <MetricBar label="Insight Acceptance" value={summary.insight_acceptance_rate} color="#14b8a6" />
                </div>
            </div>

            {/* Adoption & Usage */}
            <div style={{
                padding: '12px', borderRadius: '8px',
                background: 'rgba(30,41,59,0.6)', border: '1px solid rgba(255,255,255,0.05)',
                display: 'flex', flexDirection: 'column', gap: '8px'
            }}>
                <div style={{ fontSize: '11px', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Adoption Signals
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: '12px', color: '#cbd5e1' }}>Total Events</span>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: '#f8fafc' }}>{summary.total_events}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: '12px', color: '#cbd5e1' }}>Favorite Template</span>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: '#3b82f6' }}>{adoption?.most_used_template || 'N/A'}</span>
                </div>
            </div>

            {/* Privacy Actions */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '4px' }}>
                <button
                    onClick={handleReset}
                    style={{
                        background: 'transparent', border: 'none', color: '#475569',
                        fontSize: '10px', cursor: 'pointer', textDecoration: 'underline'
                    }}
                >
                    Clear Local Analytics
                </button>
            </div>
        </div>
    );
}

function MetricBar({ label, value, color }: { label: string, value: number, color: string }) {
    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px' }}>
                <span style={{ color: '#94a3b8' }}>{label}</span>
                <span style={{ color: '#cbd5e1', fontWeight: 500 }}>{(value * 100).toFixed(0)}%</span>
            </div>
            <div style={{ width: '100%', height: '3px', borderRadius: '1.5px', background: 'rgba(255,255,255,0.05)' }}>
                <div style={{
                    width: `${value * 100}%`, height: '100%',
                    background: color, borderRadius: '1.5px',
                    transition: 'width 0.6s cubic-bezier(0.4, 0, 0.2, 1)'
                }} />
            </div>
        </div>
    );
}
