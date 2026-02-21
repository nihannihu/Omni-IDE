// Phase 7: useCopilot — React hook for Copilot Store subscription
import { useEffect, useState } from 'react';
import copilotStore, { CopilotState } from '../stores/copilotStore';

export function useCopilot(): CopilotState {
    const [state, setState] = useState<CopilotState>(copilotStore.getState());

    useEffect(() => {
        const unsubscribe = copilotStore.subscribe((newState) => {
            setState({ ...newState });
        });
        return unsubscribe;
    }, []);

    return state;
}
