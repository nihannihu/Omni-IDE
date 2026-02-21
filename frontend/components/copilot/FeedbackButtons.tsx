'use client';
import React, { useState } from 'react';

// --- Dialog Component ---
interface FeedbackDialogProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (comment: string) => void;
}

function FeedbackDialog({ isOpen, onClose, onSubmit }: FeedbackDialogProps) {
    const [comment, setComment] = useState('');

    if (!isOpen) return null;

    return (
        <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.5)', zIndex: 100,
            display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}>
            <div style={{
                background: '#1E293B', padding: '16px', borderRadius: '12px',
                width: '320px', border: '1px solid rgba(255,255,255,0.1)',
                boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
                display: 'flex', flexDirection: 'column', gap: '12px'
            }}>
                <div style={{ fontSize: '14px', fontWeight: 600, color: '#F1F5F9' }}>
                    Provide Feedback
                </div>
                <div style={{ fontSize: '12px', color: '#94A3B8' }}>
                    Tell us why you didn't like this action.
                </div>
                <textarea
                    autoFocus
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder="Optional comment..."
                    style={{
                        width: '100%', height: '80px', background: '#0F172A',
                        border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px',
                        padding: '8px', color: '#F1F5F9', fontSize: '13px',
                        resize: 'none', outline: 'none'
                    }}
                />
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                    <button
                        onClick={onClose}
                        style={{
                            background: 'transparent', border: '1px solid rgba(255,255,255,0.2)',
                            color: '#CBD5E1', padding: '6px 12px', borderRadius: '6px',
                            fontSize: '12px', cursor: 'pointer'
                        }}
                    >
                        Cancel
                    </button>
                    <button
                        onClick={() => onSubmit(comment)}
                        style={{
                            background: '#3B82F6', border: 'none',
                            color: '#FFFFFF', padding: '6px 12px', borderRadius: '6px',
                            fontSize: '12px', cursor: 'pointer', fontWeight: 600
                        }}
                    >
                        Submit
                    </button>
                </div>
            </div>
        </div>
    );
}

// --- Main Buttons Component ---
export interface FeedbackButtonsProps {
    eventId: string;
    module: "router" | "planner" | "insight" | "copilot";
    context?: any;
}

export default function FeedbackButtons({ eventId, module, context }: FeedbackButtonsProps) {
    const [status, setStatus] = useState<'idle' | 'submitting' | 'success'>('idle');
    const [showDialog, setShowDialog] = useState(false);

    const submitFeedback = async (rating: "up" | "down", comment: string = "") => {
        try {
            setStatus('submitting');

            // Use fetch to call the backend endpoint without blocking the UI
            fetch('http://localhost:8000/api/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    event_id: eventId,
                    module: module,
                    rating: rating,
                    comment: comment || null,
                    context: context || {}
                })
            }).catch(e => console.error("Feedback submission error:", e));

            // Assume success instantly(Optimistic UI) 
            // to add zero blocking latency to main workflow
            setStatus('success');
            setTimeout(() => setStatus('idle'), 2000);
        } catch (e) {
            console.error("Failed to submit feedback", e);
            setStatus('idle');
        }
    };

    const handleUpvote = () => {
        if (status !== 'idle') return;
        submitFeedback("up");
    };

    const handleDownvote = () => {
        if (status !== 'idle') return;
        setShowDialog(true);
    };

    const handleDialogSubmit = (comment: string) => {
        setShowDialog(false);
        submitFeedback("down", comment);
    };

    if (status === 'success') {
        return (
            <div style={{ fontSize: '11px', color: '#22C55E', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ fontSize: '12px' }}>✓</span> Thanks for the feedback!
            </div>
        );
    }

    return (
        <>
            <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                <button
                    disabled={status !== 'idle'}
                    onClick={handleUpvote}
                    style={{
                        background: 'transparent', border: 'none', cursor: 'pointer',
                        padding: '2px 4px', borderRadius: '4px', display: 'flex', alignItems: 'center',
                        justifyContent: 'center', transition: 'background 0.2s',
                        opacity: status === 'idle' ? 1 : 0.5
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                    title="Helpful"
                    aria-label="Thumbs up"
                >
                    <span style={{ fontSize: '14px', filter: 'grayscale(1) brightness(1.5)' }}>👍</span>
                </button>
                <div style={{ width: '1px', height: '12px', background: 'rgba(255,255,255,0.1)' }} />
                <button
                    disabled={status !== 'idle'}
                    onClick={handleDownvote}
                    style={{
                        background: 'transparent', border: 'none', cursor: 'pointer',
                        padding: '2px 4px', borderRadius: '4px', display: 'flex', alignItems: 'center',
                        justifyContent: 'center', transition: 'background 0.2s',
                        opacity: status === 'idle' ? 1 : 0.5
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                    title="Not helpful"
                    aria-label="Thumbs down"
                >
                    <span style={{ fontSize: '14px', filter: 'grayscale(1) brightness(1.5)' }}>👎</span>
                </button>
            </div>

            <FeedbackDialog
                isOpen={showDialog}
                onClose={() => setShowDialog(false)}
                onSubmit={handleDialogSubmit}
            />
        </>
    );
}
