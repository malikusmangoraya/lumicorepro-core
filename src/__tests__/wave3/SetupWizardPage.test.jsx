import { describe, expect, it, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { AppContext } from '../../context/AppContext';
import SetupWizard from '../../pages/SetupWizard';
import settingsApi from '../../services/settingsApi';

vi.mock('../../services/settingsApi', () => ({
  default: { setup: vi.fn() },
}));

const loginMock = vi.fn();

function renderWizard() {
  return render(
    <MemoryRouter initialEntries={['/setup']}>
      <AppContext.Provider value={{ login: loginMock }}>
        <Routes>
          <Route path="/setup" element={<SetupWizard />} />
          <Route path="/dashboard" element={<div>dashboard-page</div>} />
          <Route path="/login" element={<div>login-page</div>} />
        </Routes>
      </AppContext.Provider>
    </MemoryRouter>
  );
}

function fillAdmin({
  name = 'Jane Doe',
  email = 'jane@example.com',
  password = 'password123',
  confirmPassword = 'password123',
} = {}) {
  fireEvent.change(screen.getByLabelText(/^Full Name/), { target: { value: name } });
  fireEvent.change(screen.getByLabelText(/^Admin Email/), { target: { value: email } });
  fireEvent.change(screen.getByLabelText(/^Password/), { target: { value: password } });
  fireEvent.change(screen.getByLabelText(/^Confirm Password/), {
    target: { value: confirmPassword },
  });
}

const clickContinue = () => fireEvent.click(screen.getByRole('button', { name: /Continue/ }));

function advanceToPayments() {
  fillAdmin();
  clickContinue();
  fireEvent.change(screen.getByLabelText(/^Business Name/), {
    target: { value: 'Acme Wellness' },
  });
  clickContinue();
}

describe('SetupWizard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    settingsApi.setup.mockReset();
  });

  it('renders the admin account step and the three-step progress list', () => {
    renderWizard();

    expect(screen.getByRole('heading', { level: 1, name: 'Welcome to LumicorePro' })).toBeTruthy();
    expect(screen.getByRole('list', { name: 'Setup progress' })).toBeTruthy();
    expect(screen.getByRole('heading', { name: 'Admin Account' })).toBeTruthy();
    expect(screen.getByText(/Create the master Super-Admin account/)).toBeTruthy();
    expect(screen.getByLabelText(/^Full Name/)).toBeTruthy();
    expect(screen.getByLabelText(/^Admin Email/)).toBeTruthy();
    expect(screen.getByLabelText(/^Password/)).toBeTruthy();
    expect(screen.getByLabelText(/^Confirm Password/)).toBeTruthy();
    expect(screen.getByRole('button', { name: /Continue/ })).toBeTruthy();
    expect(settingsApi.setup).not.toHaveBeenCalled();
  });

  it('blocks the first step with specific validation messages and never calls the API', () => {
    renderWizard();

    clickContinue();
    expect(screen.getByText('Admin name is required')).toBeTruthy();

    fillAdmin({ name: 'Jane Doe', email: 'not-an-email' });
    clickContinue();
    expect(screen.getByText('Valid admin email is required')).toBeTruthy();

    fillAdmin({ password: 'short', confirmPassword: 'short' });
    clickContinue();
    expect(screen.getByText('Password must be at least 8 characters')).toBeTruthy();

    fillAdmin({ password: 'password123', confirmPassword: 'different123' });
    clickContinue();
    expect(screen.getByText('Passwords do not match')).toBeTruthy();

    expect(settingsApi.setup).not.toHaveBeenCalled();
    expect(screen.getByRole('heading', { name: 'Admin Account' })).toBeTruthy();
  });

  it('advances through business details and reveals Stripe fields on demand', () => {
    renderWizard();
    fillAdmin();
    clickContinue();

    expect(screen.getByRole('heading', { name: 'Business Details' })).toBeTruthy();
    expect(screen.getByLabelText(/^Base Currency/)).toHaveValue('USD');

    clickContinue();
    expect(screen.getByText('Business name is required')).toBeTruthy();

    fireEvent.change(screen.getByLabelText(/^Business Name/), {
      target: { value: 'Acme Wellness' },
    });
    clickContinue();

    expect(screen.getByRole('heading', { name: 'Payments (Optional)' })).toBeTruthy();
    const stripeSwitch = screen.getByRole('switch', { name: 'Enable Stripe' });
    expect(stripeSwitch).not.toBeChecked();
    expect(screen.queryByLabelText('Stripe Secret Key')).toBeNull();

    fireEvent.click(stripeSwitch);

    expect(stripeSwitch).toBeChecked();
    expect(screen.getByLabelText('Stripe Secret Key')).toBeTruthy();
    expect(screen.getByLabelText('Stripe Publishable Key')).toBeTruthy();
    expect(screen.getByLabelText('Webhook Secret (optional)')).toBeTruthy();
  });

  it('submits the wizard payload, logs the admin in and redirects to the dashboard', async () => {
    settingsApi.setup.mockResolvedValue({
      token: 'jwt-token',
      user: { id: 'user-1', email: 'jane@example.com' },
    });
    renderWizard();
    advanceToPayments();

    fireEvent.click(screen.getByRole('button', { name: /Finish Setup/ }));

    expect(await screen.findByText('dashboard-page')).toBeTruthy();
    expect(settingsApi.setup).toHaveBeenCalledTimes(1);
    expect(settingsApi.setup).toHaveBeenCalledWith({
      admin: { name: 'Jane Doe', email: 'jane@example.com', password: 'password123' },
      business: expect.objectContaining({
        name: 'Acme Wellness',
        supportEmail: 'jane@example.com',
      }),
      currency: { code: 'USD' },
      payments: {
        stripe: expect.objectContaining({ enabled: false, mode: 'sandbox' }),
      },
    });
    expect(loginMock).toHaveBeenCalledWith(
      { id: 'user-1', email: 'jane@example.com' },
      'jwt-token'
    );
  });

  it('surfaces a setup failure without leaving the final step', async () => {
    settingsApi.setup.mockRejectedValue({
      response: { data: { error: 'Setup service unavailable' } },
    });
    renderWizard();
    advanceToPayments();

    fireEvent.click(screen.getByRole('button', { name: /Finish Setup/ }));

    expect(await screen.findByText('Setup service unavailable')).toBeTruthy();
    expect(screen.getByRole('heading', { name: 'Payments (Optional)' })).toBeTruthy();
    expect(screen.queryByText('dashboard-page')).toBeNull();
    expect(loginMock).not.toHaveBeenCalled();
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /Finish Setup/ })).toBeEnabled()
    );
  });
});
