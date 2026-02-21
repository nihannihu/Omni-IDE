'use client';
import React, { useState } from 'react';
export interface WorkflowTemplate {
    id: string;
    name: string;
    description: string;
    params: { name: string; type: string; required: boolean }[];
}

interface TemplateRunModalProps {
    template: WorkflowTemplate;
    onClose: () => void;
    onSubmit: (params: Record<string, string>) => void;
}

export default function TemplateRunModal({ template, onClose, onSubmit }: TemplateRunModalProps) {
    const [params, setParams] = useState<Record<string, string>>({});

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        // Validate required params
        for (const p of template.params) {
            if (p.required && !params[p.name]) {
                alert(`Missing required parameter: ${p.name}`);
                return;
            }
        }

        onSubmit(params);
    };

    return (
        <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.5)', zIndex: 100,
            display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}>
            <div style={{
                background: '#1E293B', padding: '20px', borderRadius: '12px',
                width: '360px', border: '1px solid rgba(255,255,255,0.1)',
                boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
                display: 'flex', flexDirection: 'column', gap: '16px'
            }}>
                <div>
                    <div style={{ fontSize: '15px', fontWeight: 600, color: '#F1F5F9' }}>
                        Run Workflow: {template.name}
                    </div>
                    <div style={{ fontSize: '12px', color: '#94A3B8', marginTop: '4px' }}>
                        Fill in the required parameters to start execution.
                    </div>
                </div>

                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {template.params.map((p: any) => (
                        <div key={p.name} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <label style={{ fontSize: '11px', color: '#CBD5E1', fontWeight: 500, textTransform: 'uppercase' }}>
                                {p.name} {p.required && <span style={{ color: '#EF4444' }}>*</span>}
                            </label>
                            <input
                                autoFocus
                                type={p.type === 'string' ? "text" : "text"}
                                value={params[p.name] || ''}
                                onChange={(e) => setParams({ ...params, [p.name]: e.target.value })}
                                style={{
                                    background: '#0F172A', border: '1px solid rgba(255,255,255,0.1)',
                                    padding: '8px', borderRadius: '6px', color: '#F1F5F9',
                                    fontSize: '13px', outline: 'none'
                                }}
                                placeholder={`Enter ${p.name}...`}
                            />
                        </div>
                    ))}

                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '8px' }}>
                        <button
                            type="button"
                            onClick={onClose}
                            style={{
                                background: 'transparent', border: '1px solid rgba(255,255,255,0.2)',
                                color: '#CBD5E1', padding: '6px 14px', borderRadius: '6px',
                                fontSize: '12px', cursor: 'pointer'
                            }}
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            style={{
                                background: '#3B82F6', border: 'none',
                                color: '#FFFFFF', padding: '6px 14px', borderRadius: '6px',
                                fontSize: '12px', cursor: 'pointer', fontWeight: 600
                            }}
                        >
                            Start Execution
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
