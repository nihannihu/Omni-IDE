import React from 'react';
import { render, screen, act, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import TemplatePanel from '../components/copilot/TemplatePanel';

// Mock fetch globally
const mockTemplates = [
    {
        id: "feature_scaffold",
        name: "Feature Scaffold",
        description: "Creates boilerplate",
        params: [
            { name: "feature_name", type: "string", required: true }
        ]
    }
];

global.fetch = jest.fn((url) => {
    if (url.includes('/api/templates/run')) {
        return Promise.resolve({
            json: () => Promise.resolve({ status: 'started' }),
        });
    }
    return Promise.resolve({
        json: () => Promise.resolve(mockTemplates),
    });
}) as jest.Mock;

describe('Phase 7 Sprint 4: Workflow Templates MVP', () => {

    beforeEach(() => {
        jest.clearAllMocks();
    });

    test('1️⃣ T1: Template Load - Fetches and renders templates', async () => {
        await act(async () => {
            render(<TemplatePanel />);
        });

        expect(screen.getByText('Feature Scaffold')).toBeInTheDocument();
        expect(screen.getByText('Creates boilerplate')).toBeInTheDocument();
    });

    test('2️⃣ T2: Parameter Validation - Blocks missing required params', async () => {
        await act(async () => {
            render(<TemplatePanel />);
        });

        // Open modal
        const runBtn = screen.getByText('Run', { selector: 'button' });
        await act(async () => { fireEvent.click(runBtn); });

        expect(screen.getByText('Run Workflow: Feature Scaffold')).toBeInTheDocument();

        // Spy on window.alert
        const alertMock = jest.spyOn(window, 'alert').mockImplementation(() => { });

        // Submit without filling params
        const submitBtn = screen.getByText('Start Execution');
        await act(async () => { fireEvent.click(submitBtn); });

        expect(alertMock).toHaveBeenCalledWith('Missing required parameter: feature_name');
        expect(global.fetch).toHaveBeenCalledTimes(1); // Only the initial GET load

        alertMock.mockRestore();
    });

    test('3️⃣ T3: Graph Execution - Submits valid params to API', async () => {
        await act(async () => {
            render(<TemplatePanel />);
        });

        // Open modal
        await act(async () => { fireEvent.click(screen.getByText('Run')); });

        // Fill param
        const input = screen.getByPlaceholderText('Enter feature_name...');
        await act(async () => {
            fireEvent.change(input, { target: { value: 'AuthModule' } });
        });

        // Submit
        await act(async () => {
            fireEvent.click(screen.getByText('Start Execution'));
        });

        // Modal should close
        expect(screen.queryByText('Run Workflow: Feature Scaffold')).not.toBeInTheDocument();

        // Fetch was called with POST
        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining('/api/templates/run'),
            expect.objectContaining({
                method: 'POST',
                body: expect.stringContaining('"template_id":"feature_scaffold"')
            })
        );
        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining('/api/templates/run'),
            expect.objectContaining({
                body: expect.stringContaining('"feature_name":"AuthModule"')
            })
        );
    });
});
