import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import LoginForm from '../../components/auth/LoginForm';

const fillCredentials = (email = 'ada@example.com', password = 'secret123') => {
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: email } });
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: password } });
};

describe('LoginForm', () => {
  it('renders labelled email and password fields with the submit action', () => {
    render(<LoginForm />);

    expect(screen.getByRole('heading', { name: 'Welcome back' })).toBeInTheDocument();
    expect(screen.getByText('Sign in to your account to continue')).toBeInTheDocument();

    const email = screen.getByLabelText('Email');
    expect(email).toHaveAttribute('type', 'email');
    expect(email).toHaveAttribute('autocomplete', 'email');
    expect(email).toBeRequired();

    const password = screen.getByLabelText('Password');
    expect(password).toHaveAttribute('type', 'password');
    expect(password).toHaveAttribute('autocomplete', 'current-password');
    expect(password).toBeRequired();

    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('calls onSubmit once with the typed credentials', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<LoginForm onSubmit={onSubmit} />);

    fillCredentials('ada@example.com', 'secret123');
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith({ email: 'ada@example.com', password: 'secret123' });
    await waitFor(() => expect(screen.getByRole('button', { name: /sign in/i })).toBeEnabled());
  });

  // Finding: the form is noValidate and never checks the fields itself, so the
  // required attributes are inert and empty credentials reach the handler.
  it('blocks submission and shows an error for empty credentials', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<LoginForm onSubmit={onSubmit} />);

    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toHaveTextContent(/valid email/i);
  });

  it('submits trimmed credentials once they are valid', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<LoginForm onSubmit={onSubmit} />);

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'buyer@example.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'Secret123' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith({ email: 'buyer@example.com', password: 'Secret123' })
    );
  });

  it('disables submit and shows a busy indicator while the handler is pending', async () => {
    let resolveSubmit;
    const onSubmit = vi.fn(
      () =>
        new Promise((resolve) => {
          resolveSubmit = resolve;
        })
    );
    render(<LoginForm onSubmit={onSubmit} />);
    fillCredentials();

    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    const pendingButton = screen.getByRole('button', { name: /sign in/i });
    expect(pendingButton).toBeDisabled();
    expect(screen.getByRole('status', { name: /loading/i })).toBeInTheDocument();

    fireEvent.click(pendingButton);
    expect(onSubmit).toHaveBeenCalledTimes(1);

    await act(async () => {
      resolveSubmit();
    });
    expect(screen.getByRole('button', { name: /sign in/i })).toBeEnabled();
  });

  it('renders a supplied error as an alert', () => {
    render(<LoginForm error="Invalid email or password" />);

    expect(screen.getByRole('alert')).toHaveTextContent('Invalid email or password');
  });

  it('invokes the forgot-password handler when provided', () => {
    const onForgotPassword = vi.fn();
    render(<LoginForm onForgotPassword={onForgotPassword} />);

    fireEvent.click(screen.getByRole('button', { name: 'Forgot password?' }));

    expect(onForgotPassword).toHaveBeenCalledOnce();
  });

  it('toggles password visibility and updates the accessible label', () => {
    render(<LoginForm />);
    const password = screen.getByLabelText('Password');
    expect(password).toHaveAttribute('type', 'password');

    fireEvent.click(screen.getByRole('button', { name: 'Show password' }));
    expect(password).toHaveAttribute('type', 'text');

    fireEvent.click(screen.getByRole('button', { name: 'Hide password' }));
    expect(password).toHaveAttribute('type', 'password');
  });

  it('supports custom copy and submit label', () => {
    render(<LoginForm title="Sign in" subtitle="Access your workspace" submitLabel="Continue" />);

    expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument();
    expect(screen.getByText('Access your workspace')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Continue' })).toBeInTheDocument();
  });
});
