// Phase 6: Timeline Store — Lightweight DAG execution state manager

export interface TimelineNodeState {
    id: string;
    status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'UNKNOWN';
}

export interface DagState {
    graphId: string;
    nodes: TimelineNodeState[];
    currentNode: string;
    progress: number;
    isActive: boolean;
}

const EMPTY_STATE: DagState = {
    graphId: '',
    nodes: [],
    currentNode: '',
    progress: 0,
    isActive: false,
};

type Listener = (state: DagState) => void;

class TimelineStore {
    private state: DagState = { ...EMPTY_STATE };
    private listeners: Set<Listener> = new Set();

    getState(): DagState {
        return this.state;
    }

    subscribe(listener: Listener): () => void {
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }

    private notify() {
        this.listeners.forEach((fn) => fn(this.state));
    }

    /** Process an incoming dag_update event from the WebSocket */
    handleDagUpdate(payload: any) {
        if (!payload || !payload.nodes) return;

        const nodes: TimelineNodeState[] = (payload.nodes || []).map((n: any) => ({
            id: n.id || 'unknown',
            status: ['PENDING', 'RUNNING', 'COMPLETED', 'FAILED'].includes(n.status)
                ? n.status
                : 'UNKNOWN',
        }));

        this.state = {
            graphId: payload.graph_id || this.state.graphId || 'dag',
            nodes,
            currentNode: payload.current_node || '',
            progress: typeof payload.progress === 'number' ? payload.progress : this.estimateProgress(nodes),
            isActive: true,
        };

        // Auto-deactivate if all nodes completed or any failed
        const allDone = nodes.every((n) => n.status === 'COMPLETED');
        const anyFailed = nodes.some((n) => n.status === 'FAILED');
        if (allDone || anyFailed) {
            // Give UI 2 seconds to show final state before fading
            setTimeout(() => {
                this.state = { ...this.state, isActive: false };
                this.notify();
            }, 2000);
        }

        this.notify();
    }

    /** Reset for a new workflow */
    reset() {
        this.state = { ...EMPTY_STATE };
        this.notify();
    }

    private estimateProgress(nodes: TimelineNodeState[]): number {
        if (nodes.length === 0) return 0;
        const completed = nodes.filter((n) => n.status === 'COMPLETED').length;
        return parseFloat((completed / nodes.length).toFixed(2));
    }
}

// Singleton export
const timelineStore = new TimelineStore();
export default timelineStore;
