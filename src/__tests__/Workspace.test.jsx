import React from 'react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { AppContext } from '../context/AppContext';
import WorkspacePage from '../pages/Workspace';
import { extensionsAPI } from '../services/api';

vi.mock('../services/api', () => ({
  extensionsAPI: {
    watchtower: vi.fn(),
    getWebhooks: vi.fn().mockResolvedValue({ data: { data: { webhooks: [] } } }),
    marketingKit: vi.fn(),
    browserQA: vi.fn(),
    checkoutStripe: vi.fn(),
    deliveryReport: vi.fn(),
    editElement: vi.fn(),
    updateWebhooks: vi.fn(),
    testWebhook: vi.fn(),
    githubPagesDeploy: vi.fn(),
  },
}));

const context = {
  addNotification: vi.fn(),
  isAuthenticated: true,
};

function renderWorkspace() {
  return render(
    <AppContext.Provider value={context}>
      <WorkspacePage />
    </AppContext.Provider>
  );
}

describe('Workspace Agent Control Center', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('renders accessible control-center tabs and preserves the persisted run ID', async () => {
    localStorage.setItem('lmc_last_run_id', 'run-123');
    extensionsAPI.watchtower.mockRejectedValueOnce(new Error('Agent backend unavailable'));

    renderWorkspace();

    expect(screen.getByRole('heading', { name: /agent control center/i })).toBeTruthy();
    expect(screen.getByText('LumicorePro / Agent OS')).toBeTruthy();
    expect(screen.getByText('Control plane ready')).toBeTruthy();
    expect(screen.getAllByRole('tab')).toHaveLength(7);

    await waitFor(() => expect(screen.getByText('Agent backend unavailable')).toBeTruthy());
    expect(screen.getByLabelText(/project run id/i)).toHaveValue('run-123');
    expect(screen.getAllByText(/analytics unavailable/i).length).toBeGreaterThan(0);
  });

  it('keeps the entered run ID when switching to an extension tab', async () => {
    extensionsAPI.watchtower.mockResolvedValueOnce({ data: { data: { pool: {}, usage: {}, health: {} } } });
    renderWorkspace();

    const input = screen.getByLabelText(/project run id/i);
    fireEvent.change(input, { target: { value: 'run-manual' } });
    fireEvent.click(screen.getByRole('tab', { name: /browser qa/i }));

    expect(screen.getByLabelText(/project run id/i)).toHaveValue('run-manual');
    expect(screen.getByRole('tab', { name: 'Browser QA' })).toBeTruthy();
  });
});
