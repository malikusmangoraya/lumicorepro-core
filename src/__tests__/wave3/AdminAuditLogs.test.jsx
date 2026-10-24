import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AdminAuditLogs from '../../pages/AdminAuditLogs';
import { downloadBlob } from '../../utils/csv';

vi.mock('../../utils/csv', () => ({ downloadBlob: vi.fn() }));

const { auditAPI } = vi.hoisted(() => ({
  auditAPI: { list: vi.fn(), exportCSV: vi.fn() },
}));

vi.mock('../../services/api', () => ({ auditAPI }));

const LOGS = [
  {
    id: 1,
    action: 'user.login',
    email: 'ada@example.com',
    ip: '203.0.113.7',
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/130 Safari/537.36',
    timestamp: '2026-10-01T10:00:00.000Z',
  },
];

const renderAuditLogs = () => {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={client}>
      <AdminAuditLogs />
    </QueryClientProvider>
  );
};

beforeEach(() => {
  vi.clearAllMocks();
  auditAPI.list.mockResolvedValue({
    data: { data: LOGS, pagination: { page: 1, totalPages: 2, total: 21 } },
  });
  auditAPI.exportCSV.mockResolvedValue({ data: 'csv-body' });
});

describe('AdminAuditLogs page', () => {
  it('renders log rows and paginates through the mocked API', async () => {
    renderAuditLogs();

    expect(await screen.findByText('user.login')).toBeInTheDocument();
    expect(screen.getByText('ada@example.com')).toBeInTheDocument();
    expect(screen.getByText('203.0.113.7')).toBeInTheDocument();
    expect(screen.getByText(/^Mozilla\/5\.0 .*\.\.\.$/)).toBeInTheDocument();
    expect(screen.getByText('Page 1 of 2')).toBeInTheDocument();

    const prev = screen.getByRole('button', { name: 'Prev' });
    const next = screen.getByRole('button', { name: 'Next' });
    expect(prev).toBeDisabled();
    expect(next).toBeEnabled();

    fireEvent.click(next);

    await waitFor(() =>
      expect(auditAPI.list).toHaveBeenLastCalledWith(
        expect.objectContaining({ page: 2, limit: 20 })
      )
    );
  });

  it('renders the empty state when no logs match', async () => {
    auditAPI.list.mockResolvedValue({
      data: { data: [], pagination: { page: 1, totalPages: 1, total: 0 } },
    });
    renderAuditLogs();

    expect(await screen.findByText('No audit logs found')).toBeInTheDocument();
    expect(screen.queryByText('Page 1 of 1')).not.toBeInTheDocument();
  });

  it('renders the error state when the API fails', async () => {
    auditAPI.list.mockRejectedValue(new Error('boom'));
    renderAuditLogs();

    expect(await screen.findByText('Failed to load audit logs')).toBeInTheDocument();
  });

  it('applies and resets action/user filters', async () => {
    renderAuditLogs();
    await screen.findByText('user.login');

    fireEvent.change(screen.getByPlaceholderText('Action...'), {
      target: { value: '  user.login  ' },
    });
    fireEvent.change(screen.getByPlaceholderText('User ID...'), {
      target: { value: '7' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Search' }));

    await waitFor(() =>
      expect(auditAPI.list).toHaveBeenLastCalledWith(
        expect.objectContaining({ page: 1, action: 'user.login', userId: '7' })
      )
    );

    fireEvent.click(screen.getByRole('button', { name: 'Reset' }));

    await waitFor(() =>
      expect(auditAPI.list).toHaveBeenLastCalledWith(
        expect.objectContaining({ page: 1, action: undefined, userId: undefined })
      )
    );
  });

  it('exports the filtered CSV through the API and download helper', async () => {
    renderAuditLogs();
    await screen.findByText('user.login');

    fireEvent.click(screen.getByRole('button', { name: 'Export CSV' }));

    await waitFor(() => expect(auditAPI.exportCSV).toHaveBeenCalledTimes(1));
    await waitFor(() =>
      expect(downloadBlob).toHaveBeenCalledWith('csv-body', 'audit-logs.csv')
    );
  });
});
