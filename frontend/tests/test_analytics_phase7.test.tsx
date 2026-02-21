import React from 'react';
import { render, screen, act, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import AnalyticsPanel from '../components/copilot/AnalyticsPanel';

// Mock fetch globally
const mockSummary = {
    health_score: 0.85,
    workflow_success_rate: 0.9,
    template_adoption_rate: 0.5,
    patch_acceptance_rate: 0.8,
    insight_acceptance_rate: 0.7,
    total_events: 42
};

const mockAdoption = {
    most_used_template: "Feature Scaffold",
    template_breakdown: { "Feature Scaffold": 10, "API Mock": 2 }
};

global.fetch = jest.fn((url) => {
    if (url.includes('/api/analytics/summary')) {
        return Promise.resolve({
            json: () => Promise.resolve(mockSummary),
        });
    }
    if (url.includes('/api/analytics/workflows')) {
        return Promise.resolve({
            json: () => Promise.resolve(mockAdoption),
        });
    }
    return Promise.resolve({
        json: () => Promise.resolve({}),
    });
}) as jest.Mock;

describe('Phase 7 Sprint 5: Analytics & Iteration Loop', () => {

    beforeEach(() => {
        jest.clearAllMocks();
    });

    test('1️⃣ A5: Dashboard Rendering - Panel loads without blocking', async () => {
        await act(async () => {
            render(<AnalyticsPanel />);
        });

        // Wait for data to load
        await waitFor(() => {
            expect(screen.getByText('85%')).toBeInTheDocument();
        });

        expect(screen.getByText('System Health')).toBeInTheDocument();
        expect(screen.getByText('Workflow Success')).toBeInTheDocument();
        expect(screen.getByText('Total Events')).toBeInTheDocument();
        expect(screen.getByText('42')).toBeInTheDocument();
    });

    test('2️⃣ Metadata Visualization - Displays favorit template', async () => {
        await act(async () => {
            render(<AnalyticsPanel />);
        });

        await waitFor(() => {
            expect(screen.getByText('Feature Scaffold')).toBeInTheDocument();
        });
    });

    test('3️⃣ Health-based coloring logic', async () => {
        // Mock a sick system
        (global.fetch as jest.Mock).mockImplementationOnce(() => Promise.resolve({
            json: () => Promise.resolve({ ...mockSummary, health_score: 0.2 }),
        }));

        await act(async () => {
            render(<AnalyticsPanel />);
        });

        await waitFor(() => {
            const scoreElement = screen.getByText('20%');
            expect(scoreElement).toBeInTheDocument();
            // Check computed style color (redish)
            expect(scoreElement).toHaveStyle('color: rgb(239, 68, 68)');
        });
    });
});
