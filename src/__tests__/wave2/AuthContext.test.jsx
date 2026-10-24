import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AppProvider } from '../../context/AppContext';
import { AuthProvider, useAuth } from '../../context/AuthContext';
import authService from '../../services/auth';

vi.mock('../../services/auth', () => ({
  default: {
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    verifyEmail: vi.fn(),
    resendVerification: vi.fn(),
    forgotPassword: vi.fn(),
    resetPassword: vi.fn(),
    changePassword: vi.fn(),
    setup2FA: vi.fn(),
    confirm2FA: vi.fn(),
    verify2FALogin: vi.fn(),
  },
}));

const wrapper = ({ children }) => (
  <AppProvider>
    <AuthProvider>{children}</AuthProvider>
  </AppProvider>
);

const user = { id: 5, name: 'Ada Lovelace', email: 'ada@example.com', role: 'user' };

beforeEach(() => {
  localStorage.clear();
  vi.clearAllMocks();
  // jsdom 20 does not implement matchMedia; AppProvider reads the colour scheme.
  vi.stubGlobal(
    'matchMedia',
    vi.fn(() => ({
      matches: false,
      addEventListener: () => {},
      removeEventListener: () => {},
    }))
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe('AuthContext — persisted session', () => {
  it('hydrates user and token from the stored auth payload', () => {
    localStorage.setItem('auth', JSON.stringify({ user, token: 'jwt-abc' }));

    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual(user);
    expect(result.current.token).toBe('jwt-abc');
  });

  it('treats a bare auth_token as an authenticated session', () => {
    localStorage.setItem('auth_token', 'jwt-only');

    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.token).toBe('jwt-only');
    expect(result.current.user).toBeNull();
  });

  it('starts unauthenticated when nothing is stored', () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(result.current.token).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(false);
  });
});

describe('AuthContext — login', () => {
  it('logs in, delegates to the app context and persists the token', async () => {
    authService.login.mockResolvedValue({ data: { user, token: 'jwt-new' } });
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isAuthenticated).toBe(false);

    let outcome;
    await act(async () => {
      outcome = await result.current.login({ email: user.email, password: 'secret' });
    });

    expect(authService.login).toHaveBeenCalledWith({ email: user.email, password: 'secret' });
    expect(outcome).toEqual({ user, token: 'jwt-new' });
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual(user);
    expect(result.current.token).toBe('jwt-new');
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(localStorage.getItem('auth_token')).toBe('jwt-new');
    expect(JSON.parse(localStorage.getItem('auth')).user).toEqual(user);
  });

  it('supports the nested data envelope from the backend', async () => {
    authService.login.mockResolvedValue({ data: { data: { user, token: 'jwt-nested' } } });
    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login({ email: user.email, password: 'secret' });
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.token).toBe('jwt-nested');
  });

  it('returns the 2FA challenge without authenticating', async () => {
    authService.login.mockResolvedValue({
      data: { requires2FA: true, user: { id: 5 }, message: 'Enter your code' },
    });
    const { result } = renderHook(() => useAuth(), { wrapper });

    let outcome;
    await act(async () => {
      outcome = await result.current.login({ email: user.email, password: 'secret' });
    });

    expect(outcome).toEqual({
      requires2FA: true,
      user: { id: 5 },
      message: 'Enter your code',
    });
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('surfaces the API error message and rejects', async () => {
    authService.login.mockRejectedValue({ response: { data: { error: 'Invalid credentials' } } });
    const { result } = renderHook(() => useAuth(), { wrapper });

    let caught;
    await act(async () => {
      try {
        await result.current.login({ email: user.email, password: 'wrong' });
      } catch (err) {
        caught = err;
      }
    });

    expect(caught).toBeInstanceOf(Error);
    expect(caught.message).toBe('Invalid credentials');
    expect(result.current.error).toBe('Invalid credentials');
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.loading).toBe(false);
  });

  it('falls back to a generic message when the rejection has no details', async () => {
    authService.login.mockRejectedValue({});
    const { result } = renderHook(() => useAuth(), { wrapper });

    let caught;
    await act(async () => {
      try {
        await result.current.login({ email: user.email, password: 'wrong' });
      } catch (err) {
        caught = err;
      }
    });

    expect(caught.message).toBe('Login failed. Check your email and password.');
    expect(result.current.error).toBe('Login failed. Check your email and password.');
  });

  it('rejects a response that contains no token', async () => {
    authService.login.mockResolvedValue({ data: { user } });
    const { result } = renderHook(() => useAuth(), { wrapper });

    let caught;
    await act(async () => {
      try {
        await result.current.login({ email: user.email, password: 'secret' });
      } catch (err) {
        caught = err;
      }
    });

    expect(caught.message).toBe('Invalid response from authentication server');
    expect(result.current.isAuthenticated).toBe(false);
  });
});

describe('AuthContext — register and logout', () => {
  it('registers and authenticates the new user', async () => {
    authService.register.mockResolvedValue({ data: { user, token: 'jwt-register' } });
    const { result } = renderHook(() => useAuth(), { wrapper });
    const payload = { name: user.name, email: user.email, password: 'secret' };

    let outcome;
    await act(async () => {
      outcome = await result.current.register(payload);
    });

    expect(authService.register).toHaveBeenCalledWith(payload);
    expect(outcome).toEqual({ user, token: 'jwt-register' });
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual(user);
  });

  it('reports registration errors through state and rejection', async () => {
    authService.register.mockRejectedValue({
      response: { data: { message: 'Email already exists' } },
    });
    const { result } = renderHook(() => useAuth(), { wrapper });

    let caught;
    await act(async () => {
      try {
        await result.current.register({ email: user.email, password: 'secret' });
      } catch (err) {
        caught = err;
      }
    });

    expect(caught.message).toBe('Email already exists');
    expect(result.current.error).toBe('Email already exists');
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('registers without a token as a failure', async () => {
    authService.register.mockResolvedValue({ data: { user } });
    const { result } = renderHook(() => useAuth(), { wrapper });

    let caught;
    await act(async () => {
      try {
        await result.current.register({ email: user.email, password: 'secret' });
      } catch (err) {
        caught = err;
      }
    });

    expect(caught.message).toBe('Registration failed');
    expect(result.current.error).toBe('Registration failed');
  });

  it('clears the session on logout even when the API call fails', async () => {
    localStorage.setItem('auth', JSON.stringify({ user, token: 'jwt-abc' }));
    authService.logout.mockRejectedValue(new Error('offline'));
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isAuthenticated).toBe(true);

    await act(async () => {
      await result.current.logout();
    });

    expect(authService.logout).toHaveBeenCalledTimes(1);
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(result.current.token).toBeNull();
    expect(localStorage.getItem('auth')).toBeNull();
    expect(localStorage.getItem('auth_token')).toBeNull();
  });
});

describe('AuthContext — account security actions', () => {
  it('delegates verify/reset/2FA actions to the auth service', async () => {
    authService.verifyEmail.mockResolvedValue({ data: { verified: true } });
    authService.resendVerification.mockResolvedValue({ data: { sent: true } });
    authService.forgotPassword.mockResolvedValue({ data: { requested: true } });
    authService.resetPassword.mockResolvedValue({ data: { reset: true } });
    authService.changePassword.mockResolvedValue({ data: { changed: true } });
    authService.setup2FA.mockResolvedValue({ data: { secret: 'ABC123' } });
    authService.confirm2FA.mockResolvedValue({ data: { enabled: true } });
    authService.verify2FALogin.mockResolvedValue({ data: { user, token: 'jwt-2fa' } });

    const { result } = renderHook(() => useAuth(), { wrapper });
    const results = {};

    await act(async () => {
      results.verify = await result.current.verifyEmail('verify-token');
      results.resend = await result.current.resendVerification('ada@example.com');
      results.forgot = await result.current.forgotPassword('ada@example.com');
      results.reset = await result.current.resetPassword('reset-token', 'new-pass');
      results.change = await result.current.changePassword({ current: 'a', next: 'b' });
      results.setup = await result.current.setup2FA({ method: 'totp' });
      results.confirm = await result.current.confirm2FA('123456');
      results.twoFA = await result.current.verify2FALogin({ otp: '123456' });
    });

    expect(authService.verifyEmail).toHaveBeenCalledWith('verify-token');
    expect(authService.resendVerification).toHaveBeenCalledWith('ada@example.com');
    expect(authService.forgotPassword).toHaveBeenCalledWith('ada@example.com');
    expect(authService.resetPassword).toHaveBeenCalledWith('reset-token', 'new-pass');
    expect(authService.changePassword).toHaveBeenCalledWith({ current: 'a', next: 'b' });
    expect(authService.setup2FA).toHaveBeenCalledWith({ method: 'totp' });
    expect(authService.confirm2FA).toHaveBeenCalledWith('123456');
    expect(authService.verify2FALogin).toHaveBeenCalledWith({ otp: '123456' });
    expect(results).toEqual({
      verify: { verified: true },
      resend: { sent: true },
      forgot: { requested: true },
      reset: { reset: true },
      change: { changed: true },
      setup: { secret: 'ABC123' },
      confirm: { enabled: true },
      twoFA: { user, token: 'jwt-2fa' },
    });
  });
});

describe('useAuth guard', () => {
  it('throws when used outside AuthProvider', () => {
    expect(() => renderHook(() => useAuth())).toThrow('useAuth must be used within AuthProvider');
  });
});
