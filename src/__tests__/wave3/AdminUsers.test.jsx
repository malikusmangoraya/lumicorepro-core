import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AdminUsers from '../../pages/AdminUsers';

const { usersAPI } = vi.hoisted(() => ({
  usersAPI: {
    getAll: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock('../../services/api', () => ({ usersAPI }));

const USERS = [
  {
    id: 1,
    name: 'Ada Lovelace',
    email: 'ada@example.com',
    role: 'admin',
    createdAt: '2026-01-15T00:00:00.000Z',
  },
  {
    id: 2,
    name: 'Grace Hopper',
    email: 'grace@example.com',
    role: 'user',
    createdAt: '2026-02-20T00:00:00.000Z',
  },
];

const renderAdminUsers = () => {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={client}>
      <AdminUsers />
    </QueryClientProvider>
  );
};

beforeEach(() => {
  vi.clearAllMocks();
  usersAPI.getAll.mockResolvedValue({ data: { data: USERS } });
  usersAPI.create.mockResolvedValue({ data: { data: { id: 3 } } });
});

describe('AdminUsers page', () => {
  it('renders the user table from the mocked API', async () => {
    renderAdminUsers();

    expect(await screen.findByText('Ada Lovelace')).toBeInTheDocument();
    expect(screen.getByText('grace@example.com')).toBeInTheDocument();
    expect(screen.getByText('#1')).toBeInTheDocument();
    expect(screen.getByText('admin')).toBeInTheDocument();
    for (const header of ['ID', 'Name', 'Email', 'Role', 'Joined', 'Actions']) {
      expect(screen.getByRole('columnheader', { name: header })).toBeInTheDocument();
    }
    expect(screen.getByRole('button', { name: 'Export CSV' })).toBeInTheDocument();
    expect(usersAPI.getAll).toHaveBeenCalledTimes(1);
  });

  it('filters rows by name or email', async () => {
    renderAdminUsers();
    await screen.findByText('Ada Lovelace');

    fireEvent.change(screen.getByPlaceholderText('Search by name or email...'), {
      target: { value: 'grace' },
    });

    expect(screen.getByText('Grace Hopper')).toBeInTheDocument();
    expect(screen.queryByText('Ada Lovelace')).not.toBeInTheDocument();
  });

  it('renders the empty state when the API returns no users', async () => {
    usersAPI.getAll.mockResolvedValue({ data: { data: [] } });
    renderAdminUsers();

    expect(await screen.findByText('No users found')).toBeInTheDocument();
  });

  it('renders the error state when loading fails', async () => {
    usersAPI.getAll.mockRejectedValue(new Error('network down'));
    renderAdminUsers();

    expect(await screen.findByText('Failed to load users')).toBeInTheDocument();
    expect(screen.queryByText('Ada Lovelace')).not.toBeInTheDocument();
  });

  it('creates a user through the modal and refreshes the list', async () => {
    renderAdminUsers();
    await screen.findByText('Ada Lovelace');

    fireEvent.click(screen.getByRole('button', { name: 'Add User' }));
    const dialog = screen.getByRole('dialog');
    expect(within(dialog).getByRole('heading', { name: 'Add User' })).toBeInTheDocument();

    fireEvent.change(within(dialog).getByLabelText('Name'), {
      target: { value: 'Katherine Johnson' },
    });
    fireEvent.change(within(dialog).getByLabelText('Email'), {
      target: { value: 'katherine@example.com' },
    });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save' }));

    await waitFor(() =>
      expect(usersAPI.create).toHaveBeenCalledWith({
        name: 'Katherine Johnson',
        email: 'katherine@example.com',
        role: 'user',
      })
    );
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    await waitFor(() => expect(usersAPI.getAll).toHaveBeenCalledTimes(2));
  });
});
