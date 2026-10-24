import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Dashboard from '../../pages/Dashboard';

/** Recharts cannot measure a jsdom viewport; stub the chart tree. */
vi.mock('recharts', async () => {
  const React = await import('react');
  const Box = ({ children }) => React.createElement('div', null, children);
  const Empty = () => null;
  return {
    ResponsiveContainer: Box,
    LineChart: Box,
    Line: Empty,
    XAxis: Empty,
    YAxis: Empty,
    CartesianGrid: Empty,
    Tooltip: Empty,
    Legend: Empty,
  };
});

const { dashboardAPI } = vi.hoisted(() => ({
  dashboardAPI: { me: vi.fn(), myCharts: vi.fn() },
}));

vi.mock('../../services/api', () => ({ dashboardAPI }));

const renderDashboard = () => {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={client}>
      <Dashboard />
    </QueryClientProvider>
  );
};

const ME = {
  orders: { total: 4, spent: 120 },
  subscription: { plan: 'Pro', active: true },
  unreadNotifications: 3,
  usage: {
    limits: { ai_generation: 10, ai_chat: 5, api: 100 },
    used: { ai_generation: 3, ai_chat: 2, api: 50 },
  },
};

beforeEach(() => {
  vi.clearAllMocks();
  dashboardAPI.me.mockResolvedValue({ data: { data: ME } });
  dashboardAPI.myCharts.mockResolvedValue({ data: { data: [] } });
});

describe('Dashboard page', () => {
  it('renders order, subscription, notification and usage summaries', async () => {
    renderDashboard();

    expect(
      await screen.findByRole('heading', { level: 1, name: 'My Dashboard' })
    ).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
    expect(screen.getByText(/Total spent: \$120\.00/)).toBeInTheDocument();
    expect(screen.getByText('Pro')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText('3 / 10')).toBeInTheDocument();
    expect(screen.getByText('2 / 5')).toBeInTheDocument();
    expect(screen.getByText('50 / 100')).toBeInTheDocument();
    expect(screen.getByText('Usage This Month')).toBeInTheDocument();
    expect(dashboardAPI.myCharts).toHaveBeenCalledWith(6);
  });

  it('renders the monthly activity chart when chart data exists', async () => {
    dashboardAPI.myCharts.mockResolvedValue({
      data: {
        data: [
          { month: 'Jan', orders: 2, revenue: 100 },
          { month: 'Feb', orders: 3, revenue: 160 },
        ],
      },
    });
    renderDashboard();

    expect(await screen.findByText('Monthly Activity')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Monthly Activity' })).toBeInTheDocument();
  });

  it('shows the load error instead of empty stat cards', async () => {
    dashboardAPI.me.mockRejectedValue(new Error('boom'));
    renderDashboard();

    expect(await screen.findByText('Failed to load dashboard data')).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'My Dashboard' })).not.toBeInTheDocument();
  });
});
