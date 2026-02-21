'use client';
import React, { useState, useEffect } from 'react';
import TemplateRunModal from './TemplateRunModal';

export interface WorkflowTemplate {
    id: string;
    name: string;
    description: string;
    params: { name: string; type: string; required: boolean }[];
}

export default function TemplatePanel() {
    const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
    const [selectedTemplate, setSelectedTemplate] = useState<WorkflowTemplate | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        fetch('http://localhost:8000/api/templates')
            .then(res => res.json())
            .then(data => {
                setTemplates(data || []);
                setIsLoading(false);
            })
            .catch(err => {
                console.error("Failed to fetch templates:", err);
                setIsLoading(false);
            });
    }, []);

    const handleRun = (params: Record<string, string>) => {
        if (!selectedTemplate) return;

        // Asynchronously post the template ID + dynamically typed arguments
        // UI assumes instant success (non-blocking thread layout)
        fetch('http://localhost:8000/api/templates/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                template_id: selectedTemplate.id,
                params: params,
            })
        }).catch(err => console.error("Template run failed:", err));

        setSelectedTemplate(null);
    };

    if (isLoading) {
        return <div style={{ fontSize: '12px', color: '#94a3b8' }}>Loading workflows...</div>;
    }

    if (templates.length === 0) {
        return (
            <div style={{
                padding: '10px 14px', borderRadius: '8px',
                background: 'rgba(30,41,59,0.4)', color: '#475569',
                fontSize: '12px', fontStyle: 'italic',
            }}>
                No built-in workflows found.
            </div>
        );
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {templates.map(t => (
                <div key={t.id} style={{
                    padding: '10px 14px', borderRadius: '8px',
                    background: 'rgba(30,41,59,0.5)', border: '1px solid rgba(255,255,255,0.05)',
                    display: 'flex', flexDirection: 'column', gap: '6px'
                }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '13px', fontWeight: 600, color: '#e2e8f0' }}>{t.name}</span>
                        <button
                            onClick={() => setSelectedTemplate(t)}
                            style={{
                                background: '#3b82f6', color: 'white', border: 'none',
                                padding: '4px 10px', borderRadius: '4px', fontSize: '10px',
                                cursor: 'pointer', fontWeight: 600, textTransform: 'uppercase'
                            }}
                        >
                            Run
                        </button>
                    </div>
                    <span style={{ fontSize: '11px', color: '#94a3b8', lineHeight: 1.4 }}>{t.description}</span>
                </div>
            ))}

            {selectedTemplate && (
                <TemplateRunModal
                    template={selectedTemplate}
                    onClose={() => setSelectedTemplate(null)}
                    onSubmit={handleRun}
                />
            )}
        </div>
    );
}
