export interface PatchSession {
    session_id: string;
    file_path: string;
    status: "PENDING" | "APPLIED" | "DISCARDED";
    diff: string;
    created_at: number;
}

const API_BASE = "http://localhost:8000/api";

export const patchService = {
    /**
     * Fetches the metadata and diff payload for a specific patch session.
     */
    async fetchPatch(sessionId: string): Promise<PatchSession> {
        const res = await fetch(`${API_BASE}/patch/${sessionId}`);
        if (!res.ok) {
            throw new Error(`Failed to fetch patch: ${res.statusText}`);
        }
        const data = await res.json();
        if (data.error) {
            throw new Error(data.error);
        }
        return data as PatchSession;
    },

    /**
     * Applies the proposed patch atomically to the active filesystem.
     */
    async applyPatch(sessionId: string): Promise<boolean> {
        const res = await fetch(`${API_BASE}/patch/${sessionId}/apply`, {
            method: "POST",
        });
        if (!res.ok) {
            throw new Error(`Failed to apply patch: ${res.statusText}`);
        }
        const data = await res.json();
        if (data.error) {
            throw new Error(data.error);
        }
        return true;
    },

    /**
     * Discards the patch and releases server memory buffers.
     */
    async discardPatch(sessionId: string): Promise<boolean> {
        const res = await fetch(`${API_BASE}/patch/${sessionId}/discard`, {
            method: "POST",
        });
        if (!res.ok) {
            throw new Error(`Failed to discard patch: ${res.statusText}`);
        }
        const data = await res.json();
        if (data.error) {
            throw new Error(data.error);
        }
        return true;
    },

    /**
     * Fetches all currently PENDING active staging sessions.
     */
    async fetchActiveSessions(): Promise<PatchSession[]> {
        const res = await fetch(`${API_BASE}/staging/active-sessions`);
        if (!res.ok) {
            throw new Error(`Failed to fetch active sessions: ${res.statusText}`);
        }
        const data = await res.json();
        return data as PatchSession[];
    }
};
