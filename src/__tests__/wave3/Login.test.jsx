import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import LoginPage from '../../pages/Login';

/**
 * Login delegates credential checks to AuthContext (authService) and only uses
 * AppContext for notifications / the 2FA session hand-off, so both are mocked.
 */
const { authState, appState } = vi.hoisted(() => ({
  authState: { login: vi.fn(), verify2FALogin: vi.fn() },
  appState: { login: vi.fn(), addNotification: vi.fn() },
}));

vi.mock('../../context/AuthContext', () => ({
  useAuth: () => authState,
}));

vi.mock('../../context/AppContext', () => ({
  useAppContext: () => appState,
}));

const renderLogin = (entry = '/login') =>
  render(
    <MemoryRouter initialEntries={[entry]}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/dashboard" element={<div>dashboard-page</div>} />
        <Route path="/" element={<div>dashboard-page</div>} />
      </Routes>
    </MemoryRouter>
  );

const fill = (email = 'ada@example.com', password = 'secret123') => {
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: email } });
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: password } });
};

beforeEach(() => {
  vi.clearAllMocks();
  authState.login.mockResolvedValue({ user: { id: 1 }, token: 'jwt' });
  authState.verify2FALogin.mockResolvedValue({ user: { id: 1 }, token: 'jwt' });
});

describe('Login page', () => {
  it('renders the sign-in form and OAuth alternatives', () => {
    renderLogin();

    expect(screen.getByRole('heading', { level: 1, name: 'Welcome back' })).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toHaveAttribute('type', 'email');
    expect(screen.getByLabelText('Password')).toHaveAttribute('type', 'password');
    expect(screen.getByRole('button', { name: 'Sign In' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'GitHub' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Google' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /create one free/i })).toHaveAttribute(
      'href',
      '/register'
    );
  });

  it('blocks an empty submit before calling the auth service', () => {
    renderLogin();

    fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

    expect(screen.getByText('Email is required')).toBeInTheDocument();
    expect(screen.getByText('Password is required')).toBeInTheDocument();
    expect(authState.login).not.toHaveBeenCalled();
  });

  it('submits trimmed credentials and honours only a same-origin ?next path', async () => {
    renderLogin('/login?next=/dashboard');

    fill('  ada@example.com  ', 'secret123');
    fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

    await waitFor(() => expect(authState.login).toHaveBeenCalledTimes(1));
    expect(authState.login).toHaveBeenCalledWith({
      email: 'ada@example.com',
      password: 'secret123',
      captchaToken: null,
    });
    expect(await screen.findByText('dashboard-page')).toBeInTheDocument();
  });

  it('shows the backend error, keeps the typed email and re-enables submit', async () => {
    authState.login.mockRejectedValue({
      response: { data: { error: 'Invalid email or password' } },
    });
    renderLogin();

    fill('ada@example.com', 'wrongpass');
    fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

    expect(await screen.findByText('Invalid email or password')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toHaveValue('ada@example.com');
    expect(screen.getByRole('button', { name: 'Sign In' })).toBeEnabled();
    expect(authState.login).toHaveBeenCalledTimes(1);
  });

  it('walks through the 2FA challenge and signs the user in on a valid code', async () => {
    authState.login.mockResolvedValue({
      requires2FA: true,
      user: { email: 'ada@example.com' },
    });
    renderLogin();

    fill();
    fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

    await waitFor(() =>
      expect(appState.addNotification).toHaveBeenCalledWith(
        'Two-Factor Authentication is required for this account.',
        'info'
      )
    );
    const codeInput = screen.getByLabelText('Verification code');
    expect(screen.getByText('ada@example.com')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Verify & Sign In/i }));
    expect(screen.getAllByText('Enter the 6-digit code').length).toBeGreaterThan(0);
    expect(authState.verify2FALogin).not.toHaveBeenCalled();

    fireEvent.change(codeInput, { target: { value: '123456' } });
    fireEvent.click(screen.getByRole('button', { name: /Verify & Sign In/i }));

    await waitFor(() =>
      expect(authState.verify2FALogin).toHaveBeenCalledWith({
        email: 'ada@example.com',
        otp: '123456',
      })
    );
    expect(appState.login).toHaveBeenCalledWith({ id: 1 }, 'jwt');
    expect(await screen.findByText('dashboard-page')).toBeInTheDocument();
  });
});
