import { describe, expect, it, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AppContext } from '../../context/AppContext';
import WorkspacePage from '../../pages/Workspace';
import { extensionsAPI } from '../../services/api';

vi.mock('../../services/api', () => ({
  extensionsAPI: {
    watchtower: vi.fn(),
    getWebhooks: vi.fn(),
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

const watchtowerData = {
  data: {
    data: {
      pool: { available_count: 2, loaded_count: 3 },
      usage: { total_calls: 12, avg_latency_ms: 250 },
      health: { success_rate: 0.97 },
      per_provider: [{ provider: 'gemini', calls: 7, success: 6, avg_latency_ms: 180 }],
      evidence: [{ name: 'Browser QA', status: 'pass' }],
      workflow_agents: { planner: { status: 'completed' } },
    },
  },
};

const appContext = { addNotification: vi.fn(), isAuthenticated: true };

function renderWorkspace() {
  return render(
    <MemoryRouter>
      <AppContext.Provider value={appContext}>
        <WorkspacePage />
      </AppContext.Provider>
    </MemoryRouter>
  );
}

describe('WorkspacePage — agent control center', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    extensionsAPI.watchtower.mockResolvedValue(watchtowerData);
    extensionsAPI.getWebhooks.mockResolvedValue({ data: { data: { webhooks: [] } } });
    extensionsAPI.marketingKit.mockResolvedValue({
      data: { success: true, data: { message: 'Marketing kit generated' } },
    });
    extensionsAPI.updateWebhooks.mockResolvedValue({ data: { data: {} } });
  });

  it('renders the control-center tabs and loads watchtower analytics', async () => {
    renderWorkspace();

    expect(screen.getByRole('heading', { name: /agent control center/i })).toBeTruthy();
    expect(screen.getByText('LumicorePro / Agent OS')).toBeTruthy();
    expect(screen.getByText('Control plane ready')).toBeTruthy();
    expect(screen.getAllByRole('tab')).toHaveLength(7);
    expect(screen.getByRole('tab', { name: 'Watchtower' })).toHaveAttribute('aria-selected', 'true');

    expect(await screen.findByText('2/3')).toBeTruthy();
    expect(screen.getByText('12')).toBeTruthy();
    expect(screen.getByText('250ms')).toBeTruthy();
    expect(screen.getByText('97%')).toBeTruthy();

    const table = screen.getByRole('table');
    expect(within(table).getByText('gemini')).toBeTruthy();
    expect(within(table).getByText('180ms')).toBeTruthy();

    expect(screen.getByRole('heading', { name: 'Evidence' })).toBeTruthy();
    expect(screen.getByText('passed')).toBeTruthy();
    expect(screen.getByRole('heading', { name: 'Workflow handoffs' })).toBeTruthy();
    expect(screen.getByText('completed')).toBeTruthy();
    expect(screen.getByText('Reporting')).toBeTruthy();
  });

  it('shows a resilient analytics error and recovers on refresh', async () => {
    extensionsAPI.watchtower.mockRejectedValueOnce(new Error('Agent backend unavailable'));

    renderWorkspace();

    expect(await screen.findByText('Agent backend unavailable')).toBeTruthy();
    expect(
      screen.getByText(/Analytics unavailable\. Retry when the agent backend is reachable/)
    ).toBeTruthy();
    expect(screen.getByText('Waiting')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: /refresh/i }));

    expect(await screen.findByText('2/3')).toBeTruthy();
    expect(screen.queryByText('Agent backend unavailable')).toBeNull();
    expect(extensionsAPI.watchtower).toHaveBeenCalledTimes(2);
  });

  it('blocks run actions until a project run ID is provided', async () => {
    renderWorkspace();
    await screen.findByText('2/3');
    fireEvent.click(screen.getByRole('tab', { name: 'Marketing Kit' }));

    fireEvent.click(screen.getByRole('button', { name: 'Generate Marketing Kit' }));

    expect(
      await screen.findByText('Run ID required first — generate a project.')
    ).toBeTruthy();
    expect(extensionsAPI.marketingKit).not.toHaveBeenCalled();
  });

  it('runs an extension with the entered run ID and reports success', async () => {
    renderWorkspace();
    await screen.findByText('2/3');
    fireEvent.click(screen.getByRole('tab', { name: 'Marketing Kit' }));

    fireEvent.change(screen.getByLabelText(/project run id/i), {
      target: { value: 'run-789' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Generate Marketing Kit' }));

    expect(await screen.findByText('Marketing kit generated')).toBeTruthy();
    expect(extensionsAPI.marketingKit).toHaveBeenCalledWith('run-789');
    expect(localStorage.getItem('lmc_last_run_id')).toBe('run-789');
    expect(appContext.addNotification).toHaveBeenCalledWith(
      expect.stringContaining('marketing finished')
    );
    expect(screen.getByText('Ready')).toBeTruthy();
  });

  it('swaps the panel for each workspace tab', async () => {
    renderWorkspace();
    await screen.findByText('2/3');

    fireEvent.click(screen.getByRole('tab', { name: 'Browser QA' }));
    expect(screen.getByRole('heading', { name: 'Browser QA' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Run Browser QA' })).toBeTruthy();

    fireEvent.click(screen.getByRole('tab', { name: 'Stripe Checkout' }));
    expect(screen.getByRole('heading', { name: 'Stripe Checkout' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Scaffold Stripe Checkout' })).toBeTruthy();

    fireEvent.click(screen.getByRole('tab', { name: 'Visual Editor' }));
    expect(screen.getByRole('heading', { name: 'Visual Editor' })).toBeTruthy();
    expect(screen.getByRole('button', { name: /Apply AI Edit/ })).toBeTruthy();
    expect(screen.getByRole('tab', { name: 'Visual Editor' })).toHaveAttribute(
      'aria-selected',
      'true'
    );
  });

  it('loads and saves outbound webhooks on the webhooks tab', async () => {
    extensionsAPI.getWebhooks.mockResolvedValueOnce({
      data: { data: { webhooks: ['https://hooks.example/old'] } },
    });

    renderWorkspace();
    await screen.findByText('2/3');
    fireEvent.click(screen.getByRole('tab', { name: 'Webhooks' }));

    const editor = await screen.findByPlaceholderText(/hooks\.zapier\.com/);
    expect(extensionsAPI.getWebhooks).toHaveBeenCalledTimes(1);
    expect(editor).toHaveValue('https://hooks.example/old');

    fireEvent.change(editor, {
      target: { value: 'https://one.example/hook\nhttps://two.example/hook' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Save Webhooks/ }));

    await waitFor(() =>
      expect(extensionsAPI.updateWebhooks).toHaveBeenCalledWith([
        'https://one.example/hook',
        'https://two.example/hook',
      ])
    );
    expect(await screen.findByText('Saved 2 webhook endpoint(s).')).toBeTruthy();
    expect(appContext.addNotification).toHaveBeenCalledWith('Webhooks saved.');
  });
});
