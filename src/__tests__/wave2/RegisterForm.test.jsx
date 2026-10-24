import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import RegisterForm from '../../components/auth/RegisterForm';

const VALID = {
  name: 'Ada Lovelace',
  email: 'ada@example.com',
  password: 'Str0ng!password',
  confirm: 'Str0ng!password',
};

const fillForm = (overrides = {}) => {
  const values = { ...VALID, ...overrides };
  fireEvent.change(screen.getByLabelText('Full name'), { target: { value: values.name } });
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: values.email } });
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: values.password } });
  fireEvent.change(screen.getByLabelText('Confirm password'), {
    target: { value: values.confirm },
  });
  return values;
};

describe('RegisterForm', () => {
  it('renders all required fields with the right input types', () => {
    render(<RegisterForm />);

    expect(screen.getByRole('heading', { name: 'Create an account' })).toBeInTheDocument();
    for (const label of ['Full name', 'Email', 'Password', 'Confirm password']) {
      expect(screen.getByLabelText(label)).toBeRequired();
    }
    expect(screen.getByLabelText('Email')).toHaveAttribute('type', 'email');
    expect(screen.getByLabelText('Password')).toHaveAttribute('type', 'password');
    expect(screen.getByLabelText('Password')).toHaveAttribute('minlength', '8');
    expect(screen.getByRole('checkbox', { name: /i agree/i })).toBeRequired();
  });

  it('submits the name, email and password payload once', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<RegisterForm onSubmit={onSubmit} />);

    const values = fillForm();
    fireEvent.click(screen.getByRole('checkbox', { name: /i agree/i }));
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith({
      name: values.name,
      email: values.email,
      password: values.password,
    });
    expect(onSubmit.mock.calls[0][0]).not.toHaveProperty('confirm');
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /create account/i })).toBeEnabled()
    );
  });

  // Finding: `agree` is collected but never checked and the form is noValidate,
  // so the required checkbox is inert and registration proceeds without consent.
  it('blocks submission until the terms are accepted', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<RegisterForm onSubmit={onSubmit} />);

    fillForm();
    const checkbox = screen.getByRole('checkbox', { name: /i agree/i });
    expect(checkbox).not.toBeChecked();

    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toHaveTextContent(/accept the terms/i);

    fireEvent.click(checkbox);
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));
    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
  });

  it('reports a password mismatch and disables submit until it is fixed', () => {
    const onSubmit = vi.fn();
    render(<RegisterForm onSubmit={onSubmit} />);

    fillForm({ confirm: 'Different0!' });

    expect(screen.getByRole('alert')).toHaveTextContent('Passwords do not match.');
    expect(screen.getByLabelText('Confirm password')).toHaveAttribute('aria-invalid', 'true');

    const submit = screen.getByRole('button', { name: /create account/i });
    expect(submit).toBeDisabled();
    fireEvent.click(submit);
    expect(onSubmit).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText('Confirm password'), {
      target: { value: VALID.password },
    });
    expect(screen.queryByRole('alert')).toBeNull();
    expect(screen.getByRole('button', { name: /create account/i })).toBeEnabled();
  });

  it('updates the password strength meter as the password changes', () => {
    render(<RegisterForm />);
    const password = screen.getByLabelText('Password');

    expect(screen.queryByText(/^Strength:/)).toBeNull();

    fireEvent.change(password, { target: { value: 'abc' } });
    expect(screen.getByText('Strength: Weak')).toBeInTheDocument();
    expect(screen.getByLabelText('Password strength: Weak')).toBeInTheDocument();

    fireEvent.change(password, { target: { value: 'Str0ng!Password123' } });
    expect(screen.getByText('Strength: Strong')).toBeInTheDocument();
    expect(screen.getByLabelText('Password strength: Strong')).toBeInTheDocument();
  });

  it('toggles visibility for both password fields', () => {
    render(<RegisterForm />);

    fireEvent.click(screen.getByRole('button', { name: 'Show password' }));

    expect(screen.getByLabelText('Password')).toHaveAttribute('type', 'text');
    expect(screen.getByLabelText('Confirm password')).toHaveAttribute('type', 'text');

    fireEvent.click(screen.getByRole('button', { name: 'Hide password' }));
    expect(screen.getByLabelText('Password')).toHaveAttribute('type', 'password');
  });

  it('renders a supplied error as an alert and invokes the login link', () => {
    const onLogin = vi.fn();
    render(<RegisterForm onLogin={onLogin} error="Email already registered" />);

    expect(screen.getByRole('alert')).toHaveTextContent('Email already registered');
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));
    expect(onLogin).toHaveBeenCalledOnce();
  });
});
