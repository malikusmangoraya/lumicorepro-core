import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import AuthContext from '../../context/AuthContext';
import ResetPasswordPage from '../../pages/ResetPassword';

/**
 * The page passes ready-made JSX elements to leftIcon/rightIcon, which the real
 * Input/Button reject (React "Element type is invalid"). Strip those decorative
 * props so the form logic can be exercised; see the bug report for details.
 */
vi.mock('@/components/ui', async (importOriginal) => {
  const actual = await importOriginal();
  const React = await import('react');
  const withoutIcons = (props) => {
    const next = { ...props };
    delete next.leftIcon;
    delete next.rightIcon;
    return next;
  };
  const Input = (props) => React.createElement(actual.Input, withoutIcons(props));
  const Button = (props) => React.createElement(actual.Button, withoutIcons(props));
  return { ...actual, Input, Button };
});

const renderPage = (token, overrides = {}) => {
  const auth = {
    resetPassword: vi.fn().mockResolvedValue({}),
    ...overrides,
  };
  const entry = token ? `/reset-password/${token}` : '/reset-password';
  render(
    <MemoryRouter initialEntries={[entry]}>
      <AuthContext.Provider value={auth}>
        <Routes>
          <Route path="/reset-password/:token?" element={<ResetPasswordPage />} />
          <Route path="/login" element={<div>login-page</div>} />
        </Routes>
      </AuthContext.Provider>
    </MemoryRouter>
  );
  return auth;
};

const fillPasswords = (password, confirm) => {
  fireEvent.change(screen.getByLabelText('New password'), { target: { value: password } });
  fireEvent.change(screen.getByLabelText('Confirm password'), { target: { value: confirm } });
};

const submit = () =>
  fireEvent.click(screen.getByRole('button', { name: /update password/i }));

describe('ResetPassword page', () => {
  it('warns and disables submission when the reset token is missing', () => {
    renderPage();

    expect(screen.getByText(/Missing reset token/)).toBeTruthy();
    expect(screen.getByRole('button', { name: /update password/i })).toBeDisabled();
  });

  it('renders both password fields when a token is present', () => {
    renderPage('abc123');

    expect(screen.getByRole('heading', { level: 1, name: /reset password/i })).toBeTruthy();
    expect(screen.getByLabelText('New password')).toHaveAttribute('type', 'password');
    expect(screen.getByLabelText('Confirm password')).toHaveAttribute('type', 'password');
    expect(screen.queryByText(/Missing reset token/)).toBeNull();
    expect(screen.getByRole('button', { name: /update password/i })).toBeEnabled();
  });

  it('rejects passwords shorter than six characters', () => {
    const auth = renderPage('abc123');

    fillPasswords('12345', '12345');
    submit();

    expect(
      screen.getAllByText('Password must be at least 6 characters').length
    ).toBeGreaterThan(0);
    expect(auth.resetPassword).not.toHaveBeenCalled();
  });

  it('rejects mismatched password confirmation', () => {
    const auth = renderPage('abc123');

    fillPasswords('secret1', 'secret2');
    submit();

    expect(screen.getAllByText('Passwords do not match').length).toBeGreaterThan(0);
    expect(auth.resetPassword).not.toHaveBeenCalled();
  });

  it('submits the token and new password once, then shows the success state', async () => {
    const auth = renderPage('abc123');

    fillPasswords('secret123', 'secret123');
    submit();

    await waitFor(() => {
      expect(auth.resetPassword).toHaveBeenCalledTimes(1);
    });
    expect(auth.resetPassword).toHaveBeenCalledWith('abc123', 'secret123');
    expect(
      await screen.findByText('Password updated successfully. You can sign in now.')
    ).toBeTruthy();
    expect(screen.getByRole('link', { name: /go to sign in/i })).toHaveAttribute(
      'href',
      '/login'
    );
  });

  it('surfaces the backend error when the reset link is expired', async () => {
    const auth = renderPage('expired-token', {
      resetPassword: vi
        .fn()
        .mockRejectedValue({ response: { data: { error: 'Reset token expired' } } }),
    });

    fillPasswords('secret123', 'secret123');
    submit();

    expect((await screen.findAllByText('Reset token expired')).length).toBeGreaterThan(0);
    expect(auth.resetPassword).toHaveBeenCalledTimes(1);
    expect(screen.getByRole('button', { name: /update password/i })).toBeEnabled();
  });
});
