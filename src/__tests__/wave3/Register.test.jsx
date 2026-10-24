import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import RegisterPage from '../../pages/Register';

/**
 * Register passes ready-made JSX elements to Input/Button leftIcon/rightIcon,
 * but those primitives render the prop as a component type. Strip the icons so
 * the form logic can be exercised with the real primitives (same workaround as
 * wave2/ForgotPassword). The prop misuse is reported as a bug, not masked here.
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
  return {
    ...actual,
    Input: (props) => React.createElement(actual.Input, withoutIcons(props)),
    Button: (props) => React.createElement(actual.Button, withoutIcons(props)),
  };
});

const { authState, appState } = vi.hoisted(() => ({
  authState: { register: vi.fn() },
  appState: { addNotification: vi.fn() },
}));

vi.mock('../../context/AuthContext', () => ({
  useAuth: () => authState,
}));

vi.mock('../../context/AppContext', () => ({
  useAppContext: () => appState,
}));

const renderRegister = () =>
  render(
    <MemoryRouter initialEntries={['/register']}>
      <Routes>
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/" element={<div>home-page</div>} />
      </Routes>
    </MemoryRouter>
  );

const fill = ({
  name = 'Ada Lovelace',
  email = 'ada@example.com',
  password = 'Str0ng!pass',
  confirm = password,
} = {}) => {
  fireEvent.change(screen.getByLabelText(/^Full Name/), { target: { value: name } });
  fireEvent.change(screen.getByLabelText(/^Email Address/), { target: { value: email } });
  fireEvent.change(screen.getByLabelText(/^Password/), { target: { value: password } });
  fireEvent.change(screen.getByLabelText(/^Confirm Password/), { target: { value: confirm } });
};

const acceptTerms = () => fireEvent.click(screen.getByRole('checkbox'));

beforeEach(() => {
  vi.clearAllMocks();
  authState.register.mockResolvedValue({ user: { id: 1 }, token: 'jwt' });
});

describe('Register page', () => {
  it('renders the account form with every required field and legal links', () => {
    renderRegister();

    expect(screen.getByRole('heading', { level: 1, name: 'Create an account' })).toBeInTheDocument();
    for (const label of [/^Full Name/, /^Email Address/, /^Password/, /^Confirm Password/]) {
      expect(screen.getByLabelText(label)).toBeRequired();
    }
    expect(screen.getByLabelText(/^Email Address/)).toHaveAttribute('type', 'email');
    expect(screen.getByRole('checkbox')).not.toBeChecked();
    expect(screen.getByRole('button', { name: 'Create Account' })).toBeEnabled();
    expect(screen.getByRole('link', { name: 'Terms of Service' })).toHaveAttribute(
      'href',
      '/terms'
    );
    expect(screen.getByRole('link', { name: 'Privacy Policy' })).toHaveAttribute(
      'href',
      '/privacy'
    );
  });

  it('validates the empty form and the terms checkbox before calling the service', () => {
    renderRegister();

    fireEvent.click(screen.getByRole('button', { name: 'Create Account' }));

    expect(screen.getByText('Full name is required')).toBeInTheDocument();
    expect(screen.getByText('Email is required')).toBeInTheDocument();
    expect(screen.getByText('Password is required')).toBeInTheDocument();
    expect(screen.getByText('Please confirm your password')).toBeInTheDocument();
    expect(screen.getByText('You must accept the terms')).toBeInTheDocument();
    expect(authState.register).not.toHaveBeenCalled();
  });

  it('flags a password mismatch, shows the strength meter and still requires consent', () => {
    renderRegister();

    fill({ password: 'Str0ng!pass', confirm: 'different' });
    fireEvent.click(screen.getByRole('button', { name: 'Create Account' }));

    expect(screen.getByText('Passwords do not match')).toBeInTheDocument();
    expect(screen.getByText('You must accept the terms')).toBeInTheDocument();
    expect(screen.getByText('Strong')).toBeInTheDocument();
    expect(authState.register).not.toHaveBeenCalled();
  });

  it('submits trimmed values once, notifies and navigates home', async () => {
    renderRegister();

    fill({ name: '  Ada Lovelace  ', email: '  ada@example.com  ' });
    acceptTerms();
    fireEvent.click(screen.getByRole('button', { name: 'Create Account' }));

    await waitFor(() => expect(authState.register).toHaveBeenCalledTimes(1));
    expect(authState.register).toHaveBeenCalledWith({
      name: 'Ada Lovelace',
      email: 'ada@example.com',
      password: 'Str0ng!pass',
      captchaToken: null,
    });
    expect(appState.addNotification).toHaveBeenCalledWith(
      'Account created successfully! Welcome to LumiCorePro.',
      'success'
    );
    expect(await screen.findByText('home-page')).toBeInTheDocument();
  });

  it('surfaces a backend error and leaves the form usable', async () => {
    authState.register.mockRejectedValue({
      response: { data: { error: { message: 'Email already registered' } } },
    });
    renderRegister();

    fill();
    acceptTerms();
    fireEvent.click(screen.getByRole('button', { name: 'Create Account' }));

    expect(await screen.findByText('Email already registered')).toBeInTheDocument();
    expect(authState.register).toHaveBeenCalledTimes(1);
    expect(screen.getByRole('button', { name: 'Create Account' })).toBeEnabled();
    expect(screen.getByLabelText(/^Email Address/)).toHaveValue('ada@example.com');
  });
});
