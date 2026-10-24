import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const checkHealth = vi.hoisted(() => vi.fn());

vi.mock('../../services/api', () => ({
  aiAgentAPI: { checkHealth },
}));

import CommandCenter from '../../components/common/CommandCenter';

function LocationProbe() {
  const location = useLocation();
  return <div data-testid="location">{`${location.pathname}${location.search}`}</div>;
}

function renderCenter() {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <CommandCenter />
      <LocationProbe />
    </MemoryRouter>
  );
}

beforeEach(() => {
  checkHealth.mockReset();
  // Never resolves unless a test overrides it, so unrelated tests stay act-clean.
  checkHealth.mockReturnValue(new Promise(() => {}));
});

describe('CommandCenter', () => {
  it('reports the agent as online when the health check succeeds', async () => {
    checkHealth.mockResolvedValue({ status: 200 });
    renderCenter();

    expect(await screen.findByText('Agent online')).toBeInTheDocument();
    expect(checkHealth).toHaveBeenCalled();
  });

  it('reports the agent as offline when the health check fails', async () => {
    checkHealth.mockRejectedValue(new Error('connection refused'));
    renderCenter();

    expect(await screen.findByText('Agent offline')).toBeInTheDocument();
  });

  it('submits the trimmed prompt into the chat route on Enter', () => {
    renderCenter();
    const textarea = screen.getByRole('textbox');

    fireEvent.change(textarea, { target: { value: '  Build a store with checkout  ' } });
    fireEvent.keyDown(textarea, { key: 'Enter' });

    expect(screen.getByTestId('location')).toHaveTextContent(
      '/chat?prompt=Build%20a%20store%20with%20checkout&go=1'
    );
  });

  it('does not submit on Shift+Enter, allowing multi-line prompts', () => {
    renderCenter();
    const textarea = screen.getByRole('textbox');

    fireEvent.change(textarea, { target: { value: 'line one' } });
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true });

    expect(screen.getByTestId('location')).toHaveTextContent('/');
    expect(textarea).toHaveValue('line one');
  });

  it('fills the prompt from a suggestion chip and submits with the Send button', () => {
    renderCenter();
    const textarea = screen.getByRole('textbox');

    fireEvent.click(screen.getByRole('button', { name: 'SaaS landing page' }));
    expect(textarea).toHaveValue(
      'Generate a conversion-focused landing page for a SaaS analytics product'
    );

    fireEvent.click(screen.getByRole('button', { name: 'Send' }));
    expect(screen.getByTestId('location')).toHaveTextContent(
      '/chat?prompt=Generate%20a%20conversion-focused%20landing%20page%20for%20a%20SaaS%20analytics%20product&go=1'
    );
  });

  it('focuses the prompt with Ctrl+K', () => {
    renderCenter();
    const textarea = screen.getByRole('textbox');

    fireEvent.keyDown(window, { key: 'k', ctrlKey: true });

    expect(document.activeElement).toBe(textarea);
  });
});
