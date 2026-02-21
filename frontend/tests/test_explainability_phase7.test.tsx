import React from 'react';
import { render, screen, act, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import CopilotPanel from '../components/CopilotPanel';
import copilotStore from '../stores/copilotStore';

// Mock matchMedia for UI rendering
window.matchMedia = window.matchMedia || function () {
    return {
        matches: false,
        addListener: function () { },
        removeListener: function () { }
    };
};

describe('Phase 7 Sprint 2: Explainability Events MVP', () => {

    beforeEach(() => {
        copilotStore.reset();
        jest.useFakeTimers();
    });

    afterEach(() => {
        jest.useRealTimers();
        jest.clearAllMocks();
    });

    test('1️⃣ ExplainabilityFeed renders empty state placeholder', async () => {
        await act(async () => { render(<CopilotPanel />); });

        expect(screen.getByText(/No explanations generated yet/i)).toBeInTheDocument();
    });

    test('2️⃣ ExplainabilityFeed prepends chronologically and truncates at 3', async () => {
        await act(async () => { render(<CopilotPanel />); });

        act(() => {
            copilotStore.pushExplainability({ source: 'router', reason_code: 'intent_classification', summary: 'Router test event 1' });
            copilotStore.pushExplainability({ source: 'planner', reason_code: 'dag_selection', summary: 'Planner test event 2' });
            copilotStore.pushExplainability({ source: 'insights', reason_code: 'insight_trigger', summary: 'Insights test event 3' });
            copilotStore.pushExplainability({ source: 'orchestrator', reason_code: 'node_execution', summary: 'Orchestrator test event 4' });
            jest.advanceTimersByTime(100);
        });

        // Store updates logic validation (stores 4, UI shows 3)
        const explanations = copilotStore.getState().explanations;
        expect(explanations.length).toBe(4);

        // UI reflection tests
        // The last pushed is index 0 because it's prepended
        expect(screen.getByText(/Orchestrator test event 4/i)).toBeInTheDocument();
        expect(screen.getByText(/Insights test event 3/i)).toBeInTheDocument();
        expect(screen.getByText(/Planner test event 2/i)).toBeInTheDocument();

        // Event 1 should be hidden
        expect(screen.queryByText(/Router test event 1/i)).not.toBeInTheDocument();

        // "Show X more" button should exist
        const showMoreBtn = screen.getByText(/Show 1 more/i);
        expect(showMoreBtn).toBeInTheDocument();

        // Expanding feed toggles visibility
        fireEvent.click(showMoreBtn);
        expect(screen.getByText(/Router test event 1/i)).toBeInTheDocument();
        expect(screen.getByText(/Show less/i)).toBeInTheDocument();
    });
});
