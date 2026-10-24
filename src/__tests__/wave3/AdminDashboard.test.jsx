import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AdminDashboard from '../../pages/AdminDashboard';

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
  dashboardAPI: { stats: vi.fn(), charts: vi.fn(), recentActivity: vi.fn() },
}));

vi.mock('../../services/api', () => ({ dashboardAPI }));

const renderAdminDashboard = () => {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={client}>
      <AdminDashboard />
    </QueryClientProvider>
  );
};

beforeEach(() => {
  vi.clearAllMocks();
  dashboardAPI.stats.mockResolvedValue({
    data: {
      data: { totalRevenue: 1234, totalOrders: 42, totalUsers: 900, conversionRate: 3.5 },
    },
  });
  dashboardAPI.charts.mockResolvedValue({ data: { data: [] } });
  dashboardAPI.recentActivity.mockResolvedValue({
    data: {
      data: [
        { title: 'New order', detail: 'Order #12', timestamp: '2026-10-01T10:00:00.000Z' },
      ],
    },
  });
});

describe('AdminDashboard page', () => {
  it('renders the KPI cards and recent activity from the admin API', async () => {
    renderAdminDashboard();

    expect(
      await screen.findByRole('heading', { level: 1, name: 'Admin Dashboard' })
    ).toBeInTheDocument();
    expect(screen.getByText('$1,234.00')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('900')).toBeInTheDocument();
    expect(screen.getByText('3.5%')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Revenue Trend' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'User Growth' })).toBeInTheDocument();
    expect(screen.getByText('New order')).toBeInTheDocument();
    expect(screen.getByText('Order #12')).toBeInTheDocument();
    expect(dashboardAPI.recentActivity).toHaveBeenCalledWith(5);
  });

  it('falls back to zeros and an empty activity message when data is missing', async () => {
    dashboardAPI.stats.mockResolvedValue({ data: { data: {} } });
    dashboardAPI.recentActivity.mockResolvedValue({ data: { data: [] } });
    renderAdminDashboard();

    expect(await screen.findByText('$0.00')).toBeInTheDocument();
    expect(screen.getAllByText('0').length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText('0%')).toBeInTheDocument();
    expect(screen.getByText('No recent activity')).toBeInTheDocument();
  });

  it('replaces the dashboard with an error message when stats fail', async () => {
    dashboardAPI.stats.mockRejectedValue(new Error('boom'));
    renderAdminDashboard();

    expect(await screen.findByText('Failed to load admin stats')).toBeInTheDocument();
    expect(
      screen.queryByRole('heading', { name: 'Admin Dashboard' })
    ).not.toBeInTheDocument();
  });
});
