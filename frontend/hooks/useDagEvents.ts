// Phase 6: useDagEvents — WebSocket DAG event listener hook
import { useEffect, useState, useCallback } from 'react';
import timelineStore, { DagState } from '../stores/timelineStore';

/**
 * React hook that subscribes to the TimelineStore and returns live DAG state.
 * The store is updated externally by Dashboard.tsx's WebSocket message handler.
 */
export function useDagEvents(): DagState {
    const [dagState, setDagState] = useState<DagState>(timelineStore.getState());

    useEffect(() => {
        const unsubscribe = timelineStore.subscribe((newState) => {
            setDagState({ ...newState });
        });
        return unsubscribe;
    }, []);

    return dagState;
}

/**
 * Dispatch function for use in the WebSocket message handler.
 * Call this from Dashboard.tsx when a dag_update event arrives.
 */
export function dispatchDagUpdate(payload: any): void {
    timelineStore.handleDagUpdate(payload);
}

export function resetDagTimeline(): void {
    timelineStore.reset();
}
