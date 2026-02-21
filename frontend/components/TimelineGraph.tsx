'use client';
import React from 'react';
import TimelineNode from './TimelineNode';
import { TimelineNodeState } from '../stores/timelineStore';

interface TimelineGraphProps {
    nodes: TimelineNodeState[];
    currentNode: string;
}

export default function TimelineGraph({ nodes, currentNode }: TimelineGraphProps) {
    if (!nodes || nodes.length === 0) return null;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', padding: '4px 0' }}>
            {nodes.map((node, idx) => (
                <React.Fragment key={node.id}>
                    <TimelineNode
                        id={node.id}
                        status={node.status}
                        isCurrent={node.id === currentNode}
                    />
                    {idx < nodes.length - 1 && (
                        <div
                            style={{
                                width: '2px',
                                height: '14px',
                                background: node.status === 'COMPLETED' ? '#22c55e' : '#334155',
                                marginLeft: '21px',
                                transition: 'background 0.3s ease',
                            }}
                        />
                    )}
                </React.Fragment>
            ))}
        </div>
    );
}
