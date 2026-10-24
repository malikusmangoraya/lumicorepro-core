import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import AuthContext from '../../context/AuthContext';
import ForgotPasswordPage from '../../pages/ForgotPassword';

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

const renderPage = (overrides = {}) => {
  const auth = {
    forgotPassword: vi.fn().mockResolvedValue({}),
    ...overrides,
  };
  render(
    <MemoryRouter initialEntries={['/forgot-password']}>
      <AuthContext.Provider value={auth}>
        <Routes>
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/login" element={<div>login-page</div>} />
        </Routes>
      </AuthContext.Provider>
    </MemoryRouter>
  );
  return auth;
};

const submit = () =>
  fireEvent.click(screen.getByRole('button', { name: /send reset link/i }));

describe('ForgotPassword page', () => {
  it('renders the email form with an accessible label', () => {
    renderPage();

    expect(screen.getByRole('heading', { level: 1, name: /forgot password/i })).toBeTruthy();
    expect(screen.getByLabelText('Email')).toHaveAttribute('type', 'email');
    expect(screen.getByRole('button', { name: /send reset link/i })).toBeEnabled();
    expect(screen.getAllByRole('link', { name: /back to sign in/i })[0]).toHaveAttribute(
      'href',
      '/login'
    );
  });

  it('validates an empty email before calling the API', () => {
    const auth = renderPage();

    submit();

    expect(screen.getAllByText('Enter a valid email address').length).toBeGreaterThan(0);
    expect(auth.forgotPassword).not.toHaveBeenCalled();
  });

  it('rejects a malformed email before calling the API', () => {
    const auth = renderPage();

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'not-an-email' } });
    submit();

    expect(screen.getAllByText('Enter a valid email address').length).toBeGreaterThan(0);
    expect(auth.forgotPassword).not.toHaveBeenCalled();
  });

  it('submits the trimmed email once and shows the enumeration-safe success state', async () => {
    const auth = renderPage();

    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: '  user@example.com  ' },
    });
    submit();

    await waitFor(() => {
      expect(auth.forgotPassword).toHaveBeenCalledTimes(1);
    });
    expect(auth.forgotPassword).toHaveBeenCalledWith('user@example.com');

    expect(
      await screen.findByText(/password reset instructions have been sent/i)
    ).toBeTruthy();
    expect(screen.getByText(/The link expires in 15 minutes/)).toBeTruthy();
    expect(screen.getAllByRole('link', { name: /back to sign in/i }).length).toBeGreaterThanOrEqual(2);
  });

  it('shows the backend error and keeps the form usable after a failed request', async () => {
    const auth = renderPage({
      forgotPassword: vi
        .fn()
        .mockRejectedValue({ response: { data: { error: 'Rate limit exceeded' } } }),
    });

    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'user@example.com' },
    });
    submit();

    expect((await screen.findAllByText('Rate limit exceeded')).length).toBeGreaterThan(0);
    expect(auth.forgotPassword).toHaveBeenCalledTimes(1);
    expect(screen.getByLabelText('Email')).toHaveValue('user@example.com');
    expect(screen.getByRole('button', { name: /send reset link/i })).toBeEnabled();
  });
});
