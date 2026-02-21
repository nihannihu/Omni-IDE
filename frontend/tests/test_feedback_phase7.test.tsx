import React from 'react';
import { render, screen, act, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import FeedbackButtons from '../components/copilot/FeedbackButtons';

// Mock fetch globally
global.fetch = jest.fn(() =>
    Promise.resolve({
        json: () => Promise.resolve({ status: 'success' }),
    })
) as jest.Mock;

describe('Phase 7 Sprint 3: Feedback Capture System MVP', () => {

    beforeEach(() => {
        jest.useFakeTimers();
        (global.fetch as jest.Mock).mockClear();
    });

    afterEach(() => {
        jest.useRealTimers();
    });

    test('1️⃣ Submit 👍 feedback -> record saved instantly (Optimistic UI)', async () => {
        render(<FeedbackButtons eventId="test_id" module="router" />);

        const upvoteBtn = screen.getByTitle('Helpful');

        await act(async () => {
            fireEvent.click(upvoteBtn);
        });

        // Fetch is called non-blocking
        expect(global.fetch).toHaveBeenCalledTimes(1);
        expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/feedback', expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('"rating":"up"')
        }));

        // UI instantly updates to success
        expect(screen.getByText(/Thanks for the feedback!/i)).toBeInTheDocument();
    });

    test('2️⃣ Submit 👎 opens comment dialog -> submit persists', async () => {
        render(<FeedbackButtons eventId="test_id_2" module="planner" context={{ step: 2 }} />);

        const downvoteBtn = screen.getByTitle('Not helpful');

        // Click opens dialog
        act(() => { fireEvent.click(downvoteBtn); });

        expect(screen.getByText(/Provide Feedback/i)).toBeInTheDocument();
        const textarea = screen.getByPlaceholderText(/Optional comment.../i);

        // Type comment
        act(() => {
            fireEvent.change(textarea, { target: { value: 'Bad AI plan' } });
        });

        // Submit
        const submitBtn = screen.getByText('Submit');
        await act(async () => {
            fireEvent.click(submitBtn);
        });

        // Dialog closes, Fetch triggered
        expect(screen.queryByText(/Provide Feedback/i)).not.toBeInTheDocument();
        expect(global.fetch).toHaveBeenCalledTimes(1);
        expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/feedback', expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('"rating":"down"')
        }));
        expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/feedback', expect.objectContaining({
            body: expect.stringContaining('"comment":"Bad AI plan"')
        }));

        // Optimistic UI success message
        expect(screen.getByText(/Thanks for the feedback!/i)).toBeInTheDocument();
    });

    test('3️⃣ Feedback resets to idle after 2 seconds', async () => {
        render(<FeedbackButtons eventId="test_reset" module="insight" />);

        const upvoteBtn = screen.getByTitle('Helpful');
        await act(async () => { fireEvent.click(upvoteBtn); });

        // Shows success
        expect(screen.getByText(/Thanks for the feedback!/i)).toBeInTheDocument();

        // Advance timers by 2 seconds
        act(() => {
            jest.advanceTimersByTime(2000);
        });

        // Expect it to revert back to buttons
        expect(screen.queryByText(/Thanks for the feedback!/i)).not.toBeInTheDocument();
        expect(screen.getByTitle('Helpful')).toBeInTheDocument();
    });
});
