import { afterEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import AuthContext from '../../context/AuthContext';
import VerifyEmailPage from '../../pages/VerifyEmail';

const renderPage = (token, overrides = {}) => {
  const auth = {
    verifyEmail: vi.fn().mockResolvedValue({}),
    resendVerification: vi.fn().mockResolvedValue({}),
    ...overrides,
  };
  render(
    <MemoryRouter initialEntries={[`/verify-email/${token}`]}>
      <AuthContext.Provider value={auth}>
        <Routes>
          <Route path="/verify-email/:token" element={<VerifyEmailPage />} />
          <Route path="/login" element={<div>login-page</div>} />
        </Routes>
      </AuthContext.Provider>
    </MemoryRouter>
  );
  return auth;
};

afterEach(() => {
  vi.restoreAllMocks();
});

describe('VerifyEmail page', () => {
  it('verifies the route token once and shows the success state', async () => {
    const auth = renderPage('tok-123', {
      verifyEmail: vi.fn().mockResolvedValue({ message: 'Email verified. Welcome!' }),
    });

    expect(
      await screen.findByRole('heading', { level: 1, name: 'Email verified' })
    ).toBeTruthy();
    expect(auth.verifyEmail).toHaveBeenCalledTimes(1);
    expect(auth.verifyEmail).toHaveBeenCalledWith('tok-123');
    expect(screen.getByText('Email verified. Welcome!')).toBeTruthy();
    expect(screen.getByRole('link', { name: /continue to sign in/i })).toHaveAttribute(
      'href',
      '/login'
    );
  });

  it('falls back to a default success message when the API omits one', async () => {
    renderPage('tok-123');

    expect(await screen.findByText('Email verified successfully')).toBeTruthy();
    expect(screen.getByText('Your account is now fully secure.')).toBeTruthy();
  });

  it('shows the verification failure and the resend control', async () => {
    const auth = renderPage('expired-token', {
      verifyEmail: vi
        .fn()
        .mockRejectedValue({ response: { data: { error: 'Token expired' } } }),
    });

    expect(
      await screen.findByRole('heading', { level: 1, name: 'Verification failed' })
    ).toBeTruthy();
    expect(screen.getByText('Token expired')).toBeTruthy();
    expect(auth.verifyEmail).toHaveBeenCalledWith('expired-token');
    expect(
      screen.getByRole('button', { name: /resend verification email/i })
    ).toBeTruthy();
    expect(screen.queryByRole('link', { name: /continue to sign in/i })).toBeNull();
  });

  it('resends the verification email to the trimmed address from the prompt', async () => {
    const auth = renderPage('expired-token', {
      verifyEmail: vi.fn().mockRejectedValue(new Error('Expired')),
    });
    vi.spyOn(window, 'prompt').mockReturnValue('  user@example.com  ');

    await screen.findByRole('heading', { level: 1, name: 'Verification failed' });
    fireEvent.click(screen.getByRole('button', { name: /resend verification email/i }));

    await waitFor(() => {
      expect(auth.resendVerification).toHaveBeenCalledTimes(1);
    });
    expect(auth.resendVerification).toHaveBeenCalledWith('user@example.com');
    expect(
      await screen.findByText('If an account exists, a new verification link has been sent.')
    ).toBeTruthy();
  });

  it('does nothing when the resend prompt is cancelled', async () => {
    const auth = renderPage('expired-token', {
      verifyEmail: vi.fn().mockRejectedValue(new Error('Expired')),
    });
    vi.spyOn(window, 'prompt').mockReturnValue(null);

    await screen.findByRole('heading', { level: 1, name: 'Verification failed' });
    fireEvent.click(screen.getByRole('button', { name: /resend verification email/i }));

    expect(auth.resendVerification).not.toHaveBeenCalled();
    expect(screen.getByText('Expired')).toBeTruthy();
  });
});
