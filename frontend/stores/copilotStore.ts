// Phase 7: Copilot Store — Unified event aggregator for the observability panel

export interface CopilotIntent {
    label: string;
    confidence: number;
    explanation: string;
    timestamp: number;
}

export interface CopilotExecution {
    graphName: string;
    completedNodes: number;
    totalNodes: number;
    currentNode: string;
    progress: number;
    isActive: boolean;
    templateContext?: any;
}

export interface CopilotInsight {
    id: string;
    title: string;
    severity: 'low' | 'medium' | 'high';
    timestamp: number;
}

export interface ExplainabilityEvent {
    id: string;
    timestamp: number;
    source: string;
    reasonCode: string;
    summary: string;
}

export type CopilotStatus = 'idle' | 'planning' | 'executing' | 'waiting';

export interface CopilotState {
    status: CopilotStatus;
    intent: CopilotIntent | null;
    execution: CopilotExecution | null;
    insights: CopilotInsight[];
    explanations: ExplainabilityEvent[];
    lastUpdated: number;
}

const EMPTY_STATE: CopilotState = {
    status: 'idle',
    intent: null,
    execution: null,
    insights: [],
    explanations: [],
    lastUpdated: 0,
};

type CopilotListener = (state: CopilotState) => void;

class CopilotStore {
    private state: CopilotState = { ...EMPTY_STATE };
    private listeners: Set<CopilotListener> = new Set();
    private debounceTimer: ReturnType<typeof setTimeout> | null = null;
    private debounceMs = 80;

    getState(): CopilotState {
        return this.state;
    }

    subscribe(listener: CopilotListener): () => void {
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }

    private notify() {
        // Debounce high-frequency updates
        if (this.debounceTimer) clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            this.listeners.forEach((fn) => fn(this.state));
        }, this.debounceMs);
    }

    /** Push a router intent classification result */
    pushIntent(label: string, confidence: number, explanation: string) {
        this.state = {
            ...this.state,
            status: 'planning',
            intent: { label, confidence, explanation, timestamp: Date.now() },
            lastUpdated: Date.now(),
        };
        this.notify();
    }

    /** Push a DAG execution update */
    pushDagUpdate(payload: any) {
        if (!payload || !payload.nodes) return;

        const nodes = payload.nodes || [];
        const completed = nodes.filter((n: any) => n.status === 'COMPLETED').length;
        const total = nodes.length;
        const isActive = !nodes.every((n: any) => n.status === 'COMPLETED' || n.status === 'FAILED');

        this.state = {
            ...this.state,
            status: isActive ? 'executing' : 'idle',
            execution: {
                graphName: payload.graph_id || 'DAG',
                completedNodes: completed,
                totalNodes: total,
                currentNode: payload.current_node || '',
                progress: typeof payload.progress === 'number' ? payload.progress : (total > 0 ? completed / total : 0),
                isActive,
                templateContext: payload.template_context,
            },
            lastUpdated: Date.now(),
        };

        // Auto-clear execution after completion fade
        if (!isActive) {
            setTimeout(() => {
                this.state = { ...this.state, execution: null, status: 'idle' };
                this.notify();
            }, 3000);
        }

        this.notify();
    }

    /** Push insight events */
    pushInsights(insights: Array<{ id: string; title: string; severity: string; created_at: number }>) {
        const mapped: CopilotInsight[] = insights.slice(0, 5).map((ins) => ({
            id: ins.id,
            title: ins.title,
            severity: (ins.severity as 'low' | 'medium' | 'high') || 'low',
            timestamp: ins.created_at * 1000,
        }));

        this.state = {
            ...this.state,
            insights: mapped,
            lastUpdated: Date.now(),
        };
        this.notify();
    }

    /** Reset to idle */
    reset() {
        this.state = { ...EMPTY_STATE, lastUpdated: Date.now() };
        this.notify();
    }

    /** Push explainability events */
    pushExplainability(payload: any) {
        const newEvent: ExplainabilityEvent = {
            id: Math.random().toString(36).substring(7),
            timestamp: payload.timestamp ? new Date(payload.timestamp).getTime() : Date.now(),
            source: payload.source || 'unknown',
            reasonCode: payload.reason_code || 'unknown',
            summary: payload.summary || '',
        };

        // Keep last 10 explanations
        const explanations = [newEvent, ...this.state.explanations].slice(0, 10);

        this.state = {
            ...this.state,
            explanations,
            lastUpdated: Date.now(),
        };
        this.notify();
    }
}

const copilotStore = new CopilotStore();
export default copilotStore;
