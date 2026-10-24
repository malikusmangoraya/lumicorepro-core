import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import InviteAccept from '../../pages/InviteAccept';

const { inviteAPI } = vi.hoisted(() => ({
  inviteAPI: { resolve: vi.fn(), accept: vi.fn() },
}));

vi.mock('../../services/api', () => ({ inviteAPI }));
vi.mock('../../components/common/ThemeProvider', () => ({
  useTheme: () => ({ theme: 'light' }),
}));

const INVITE = { orgName: 'Acme Corp', email: 'ada@example.com', role: 'admin' };

const renderPage = () => {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <MemoryRouter initialEntries={['/invite/token-abc']}>
      <QueryClientProvider client={client}>
        <Routes>
          <Route path="/invite/:token" element={<InviteAccept />} />
        </Routes>
      </QueryClientProvider>
    </MemoryRouter>
  );
};

const realLocation = window.location;

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  Object.defineProperty(window, 'location', {
    configurable: true,
    value: { href: '' },
  });
  inviteAPI.resolve.mockResolvedValue({ data: { data: INVITE } });
  inviteAPI.accept.mockResolvedValue({ data: { token: 'jwt-invite' } });
});

afterEach(() => {
  Object.defineProperty(window, 'location', { configurable: true, value: realLocation });
});

describe('InviteAccept page', () => {
  it('renders the resolved invitation details and the join form', async () => {
    renderPage();

    expect(await screen.findByText('Acme Corp')).toBeInTheDocument();
    expect(screen.getByText('ada@example.com')).toBeInTheDocument();
    expect(screen.getByText('admin')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('John Doe')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Create a password')).toHaveAttribute('type', 'password');
    expect(screen.getByRole('button', { name: /Confirm & Join/ })).toBeEnabled();
    expect(inviteAPI.resolve).toHaveBeenCalledWith('token-abc');
  });

  it('toggles password visibility with an accessible label', async () => {
    renderPage();
    const password = await screen.findByPlaceholderText('Create a password');

    fireEvent.click(screen.getByRole('button', { name: 'Show password' }));
    expect(password).toHaveAttribute('type', 'text');
    fireEvent.click(screen.getByRole('button', { name: 'Hide password' }));
    expect(password).toHaveAttribute('type', 'password');
  });

  it('accepts the invite, stores the token and redirects to the dashboard', async () => {
    renderPage();
    await screen.findByText('Acme Corp');

    fireEvent.change(screen.getByPlaceholderText('John Doe'), {
      target: { value: 'Ada Lovelace' },
    });
    fireEvent.change(screen.getByPlaceholderText('Create a password'), {
      target: { value: 'Str0ng!pass' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Confirm & Join/ }));

    await waitFor(() =>
      expect(inviteAPI.accept).toHaveBeenCalledWith('token-abc', {
        name: 'Ada Lovelace',
        password: 'Str0ng!pass',
      })
    );
    await waitFor(() => expect(localStorage.getItem('token')).toBe('jwt-invite'));
    expect(window.location.href).toBe('/dashboard');
  });

  it('shows the invalid-invitation state when resolution fails', async () => {
    inviteAPI.resolve.mockRejectedValue({ response: { status: 404 } });
    renderPage();

    expect(await screen.findByText('Invalid Invitation')).toBeInTheDocument();
    expect(screen.getByText(/expired or is invalid/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Create Account' })).toHaveAttribute(
      'href',
      '/register'
    );
  });

  it('surfaces the accept error without redirecting', async () => {
    inviteAPI.accept.mockRejectedValue({
      response: { data: { message: 'Invite already used' } },
    });
    renderPage();
    await screen.findByText('Acme Corp');

    fireEvent.change(screen.getByPlaceholderText('John Doe'), {
      target: { value: 'Ada Lovelace' },
    });
    fireEvent.change(screen.getByPlaceholderText('Create a password'), {
      target: { value: 'Str0ng!pass' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Confirm & Join/ }));

    expect(await screen.findByText('Invite already used')).toBeInTheDocument();
    expect(localStorage.getItem('token')).toBeNull();
    expect(window.location.href).toBe('');
  });
});
