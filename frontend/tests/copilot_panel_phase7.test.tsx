import React from 'react';
import { render, screen, act, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import CopilotPanel from '../components/CopilotPanel';
import copilotStore from '../stores/copilotStore';

// Mock matchMedia
window.matchMedia = window.matchMedia || function () {
    return {
        matches: false,
        addListener: function () { },
        removeListener: function () { }
    };
};

describe('Phase 7 Sprint 1: CopilotPanel E2E UI Tests', () => {

    beforeEach(() => {
        copilotStore.reset();
        jest.useFakeTimers();
    });

    afterEach(() => {
        jest.useRealTimers();
        jest.clearAllMocks();
    });

    test('C1 — Panel Mounts and shows Idle state', async () => {
        await act(async () => { render(<CopilotPanel />); });

        // Header renders
        expect(screen.getByText(/Copilot/i)).toBeInTheDocument();

        // Starts in Idle mode
        expect(screen.getByText(/Idle/i)).toBeInTheDocument();
        expect(screen.getByText(/Waiting for user input…/i)).toBeInTheDocument();
        expect(screen.getByText(/No insights detected yet./i)).toBeInTheDocument();
    });

    test('C2 — Intent Reflection updates store and UI instantly', async () => {
        await act(async () => { render(<CopilotPanel />); });

        act(() => {
            copilotStore.pushIntent('Task Graph Planner', 0.95, 'High complexity detected');
            jest.advanceTimersByTime(100); // Wait for debounce
        });

        // Store updates logic
        expect(copilotStore.getState().status).toBe('planning');

        // UI reflection
        expect(screen.getByText(/Planning/i)).toBeInTheDocument();
        expect(screen.getByText(/Task Graph Planner/i)).toBeInTheDocument();
        expect(screen.getByText(/95%/i)).toBeInTheDocument();
        expect(screen.getByText(/High complexity detected/i)).toBeInTheDocument();
    });

    test('C3 — DAG Progress Sync renders execution summary', async () => {
        await act(async () => { render(<CopilotPanel />); });

        act(() => {
            copilotStore.pushDagUpdate({
                type: 'dag_update',
                graph_id: 'Test Planner',
                nodes: [
                    { id: 'step_1', status: 'COMPLETED' },
                    { id: 'step_2', status: 'RUNNING' },
                    { id: 'step_3', status: 'PENDING' }
                ],
                current_node: 'step_2',
                progress: 0.33
            });
            jest.advanceTimersByTime(100); // Wait for debounce
        });

        // Store active execution
        expect(copilotStore.getState().status).toBe('executing');

        // UI Reflection
        expect(screen.getByText(/Executing/i)).toBeInTheDocument();
        expect(screen.getByText(/Test Planner/i)).toBeInTheDocument();
        expect(screen.getByText(/1\/3/i)).toBeInTheDocument();
        expect(screen.getByText(/step 2/i)).toBeInTheDocument(); // Replaces underscore
    });

    test('C4 — Insight Feed pushes new insights to top', async () => {
        await act(async () => { render(<CopilotPanel />); });

        act(() => {
            copilotStore.pushInsights([
                { id: 'ins1', title: 'Large file detected', severity: 'low', created_at: 1000 },
                { id: 'ins2', title: 'Memory leak likely', severity: 'high', created_at: 1001 }
            ]);
            jest.advanceTimersByTime(100);
        });

        expect(screen.getByText(/Large file detected/i)).toBeInTheDocument();
        expect(screen.getByText(/low/i)).toBeInTheDocument();
        expect(screen.getByText(/Memory leak likely/i)).toBeInTheDocument();
        expect(screen.getByText(/high/i)).toBeInTheDocument();
    });

    test('C5 — Collapse State toggles panel visibility', async () => {
        await act(async () => { render(<CopilotPanel />); });

        // Starts expanded
        expect(screen.getByText(/System Status/i)).toBeInTheDocument();

        // Click header text to collapse
        const headerToggle = screen.getByText('Copilot');
        fireEvent.click(headerToggle);

        // Content should hide
        expect(screen.queryByText(/System Status/i)).not.toBeInTheDocument();

        // Click robot icon to expand
        const collapsedIcon = screen.getByText('🤖');
        fireEvent.click(collapsedIcon);

        // Content restores
        expect(screen.getByText(/System Status/i)).toBeInTheDocument();
    });

    test('E2 — Event Burst triggers debouncing gracefully', async () => {
        const renderSpy = jest.spyOn(copilotStore, 'getState');
        await act(async () => { render(<CopilotPanel />); });

        act(() => {
            // Rapid consecutive calls
            copilotStore.pushIntent('A', 0.5, 'Test');
            copilotStore.pushIntent('B', 0.6, 'Test');
            copilotStore.pushIntent('C', 0.7, 'Test');
            copilotStore.pushIntent('D', 0.8, 'Test');
        });

        // Debounce prevents mid-state flush
        act(() => {
            jest.advanceTimersByTime(100);
        });

        // Only the last intent should render
        expect(screen.getByText(/🎯 D/i)).toBeInTheDocument();
        expect(screen.queryByText(/🎯 A/i)).not.toBeInTheDocument();
    });

});
