import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const mocks = vi.hoisted(() => ({
  notificationsAPI: {
    getAll: vi.fn(),
    markRead: vi.fn(),
    markAllRead: vi.fn(),
  },
}));

vi.mock('../../services/api', () => ({ notificationsAPI: mocks.notificationsAPI }));
vi.mock('../../components/common/ThemeProvider', () => ({
  useTheme: () => ({ theme: 'light' }),
}));

import Notifications from '../../pages/Notifications';

const minutesAgo = (minutes) => new Date(Date.now() - minutes * 60 * 1000).toISOString();

const unreadNotification = {
  id: 1,
  title: 'Deployment complete',
  message: 'Deployment finished successfully.',
  type: 'success',
  read: false,
  link: '/workspace',
  createdAt: minutesAgo(10),
};

const readNotification = {
  id: 2,
  title: 'Token expiring',
  message: 'Rotate your API key soon.',
  type: 'warning',
  read: true,
  createdAt: minutesAgo(180),
};

const pageOf = (data, pagination = {}) => ({
  data: {
    data,
    pagination: { page: 1, totalPages: 1, total: data.length, ...pagination },
  },
});

const renderPage = () => {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={client}>
      <Notifications />
    </QueryClientProvider>
  );
};

beforeEach(() => {
  vi.clearAllMocks();
  mocks.notificationsAPI.getAll.mockResolvedValue(
    pageOf([unreadNotification, readNotification])
  );
  mocks.notificationsAPI.markRead.mockResolvedValue({ data: {} });
  mocks.notificationsAPI.markAllRead.mockResolvedValue({ data: {} });
});

describe('Notifications page', () => {
  it('renders notifications, unread affordance and the notification link', async () => {
    renderPage();

    expect(await screen.findByText('Deployment complete')).toBeTruthy();
    expect(screen.getByText('Deployment finished successfully.')).toBeTruthy();
    expect(screen.getByText('Token expiring')).toBeTruthy();
    expect(screen.getByText('10m ago')).toBeTruthy();
    expect(screen.getAllByText('Mark read')).toHaveLength(1);
    expect(screen.getByRole('link')).toHaveAttribute('href', '/workspace');
    expect(mocks.notificationsAPI.getAll).toHaveBeenCalledWith({
      page: 1,
      limit: 15,
      read: undefined,
    });
  });

  it('marks a single notification as read and refetches the list', async () => {
    let listCalls = 0;
    mocks.notificationsAPI.getAll.mockImplementation(() => {
      listCalls += 1;
      const data = listCalls === 1 ? [unreadNotification] : [
        { ...unreadNotification, read: true },
      ];
      return Promise.resolve(pageOf(data));
    });

    renderPage();
    await screen.findByText('Deployment complete');

    fireEvent.click(screen.getByRole('button', { name: 'Mark read' }));

    await waitFor(() => {
      expect(mocks.notificationsAPI.markRead).toHaveBeenCalledWith(1);
    });
    await waitFor(() => {
      expect(mocks.notificationsAPI.getAll).toHaveBeenCalledTimes(2);
    });
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: 'Mark read' })).toBeNull();
    });
  });

  it('marks every notification as read and refetches the list', async () => {
    renderPage();
    await screen.findByText('Deployment complete');

    fireEvent.click(screen.getByRole('button', { name: 'Mark all read' }));

    await waitFor(() => {
      expect(mocks.notificationsAPI.markAllRead).toHaveBeenCalledTimes(1);
    });
    await waitFor(() => {
      expect(mocks.notificationsAPI.getAll).toHaveBeenCalledTimes(2);
    });
  });

  it('shows the empty state when there are no notifications', async () => {
    mocks.notificationsAPI.getAll.mockResolvedValue(pageOf([]));

    renderPage();

    expect(await screen.findByText('No notifications found')).toBeTruthy();
    expect(screen.getByRole('heading', { level: 1, name: 'Notifications' })).toBeTruthy();
  });

  it('requests only unread notifications from the Unread tab', async () => {
    mocks.notificationsAPI.getAll.mockResolvedValue(pageOf([]));
    renderPage();
    await screen.findByText('No notifications found');

    fireEvent.click(screen.getByRole('button', { name: 'Unread' }));

    await waitFor(() => {
      expect(mocks.notificationsAPI.getAll).toHaveBeenCalledWith({
        page: 1,
        limit: 15,
        read: false,
      });
    });
  });
});
