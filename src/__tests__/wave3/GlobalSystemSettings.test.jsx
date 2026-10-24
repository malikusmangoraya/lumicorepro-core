import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import GlobalSystemSettings from '../../pages/GlobalSystemSettings';

const { appState, settingsApi } = vi.hoisted(() => ({
  appState: { user: { id: 1, role: 'admin' } },
  settingsApi: { getSystem: vi.fn(), updateSystem: vi.fn() },
}));

vi.mock('../../context/AppContext', () => ({ useAppContext: () => appState }));
vi.mock('../../services/settingsApi', () => ({ default: settingsApi }));

const SYSTEM = {
  business: {
    name: 'Acme Corp',
    tagline: 'Build faster',
    logoUrl: 'https://cdn.example.com/logo.png',
    supportEmail: 'support@acme.test',
  },
  currency: { code: 'EUR' },
  payments: {
    stripe: {
      enabled: true,
      mode: 'live',
      secretKey: 'sk_live_123',
      publishableKey: 'pk_live_123',
      webhookSecret: 'whsec_123',
    },
    paypal: { enabled: false, mode: 'sandbox', clientId: 'client', clientSecret: '' },
  },
  smtp: {
    enabled: true,
    host: 'smtp.acme.test',
    port: 465,
    secure: true,
    user: 'mailer',
    pass: '',
    fromName: 'Acme',
    fromEmail: 'no-reply@acme.test',
  },
};

const renderPage = () =>
  render(
    <MemoryRouter initialEntries={['/settings/system']}>
      <Routes>
        <Route path="/settings/system" element={<GlobalSystemSettings />} />
        <Route path="/dashboard" element={<div>dashboard-page</div>} />
      </Routes>
    </MemoryRouter>
  );

beforeEach(() => {
  vi.clearAllMocks();
  appState.user = { id: 1, role: 'admin' };
  settingsApi.getSystem.mockResolvedValue(SYSTEM);
  settingsApi.updateSystem.mockResolvedValue({});
});

describe('GlobalSystemSettings page', () => {
  it('pre-fills business, currency, payment and SMTP settings for admins', async () => {
    renderPage();

    expect(
      await screen.findByRole('heading', { level: 1, name: 'Global System Settings' })
    ).toBeInTheDocument();
    expect(await screen.findByDisplayValue('Acme Corp')).toBeInTheDocument();
    expect(screen.getByLabelText(/^Support Email/)).toHaveValue('support@acme.test');
    expect(screen.getByLabelText('Currency')).toHaveValue('EUR');
    expect(screen.getByRole('switch', { name: 'Enable Stripe' })).toBeChecked();
    expect(screen.getByRole('switch', { name: 'Enable PayPal' })).not.toBeChecked();
    expect(screen.getByLabelText('Host')).toHaveValue('smtp.acme.test');
    expect(screen.getByRole('switch', { name: 'Secure connection (TLS/SSL)' })).toBeChecked();
  });

  it('denies access to non-admin users once loading finishes', async () => {
    appState.user = { id: 2, role: 'user' };
    settingsApi.getSystem.mockResolvedValue({});
    renderPage();

    expect(
      await screen.findByText('Only admin accounts can manage system settings.')
    ).toBeInTheDocument();
    expect(screen.queryByLabelText(/^Business Name/)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Back to dashboard' }));
    expect(screen.getByText('dashboard-page')).toBeInTheDocument();
  });

  it('saves the edited form and confirms the reload', async () => {
    renderPage();
    const nameInput = await screen.findByDisplayValue('Acme Corp');

    fireEvent.change(nameInput, { target: { value: 'Acme Global' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save Settings' }));

    await waitFor(() => expect(settingsApi.updateSystem).toHaveBeenCalledTimes(1));
    const payload = settingsApi.updateSystem.mock.calls[0][0];
    expect(payload.business.name).toBe('Acme Global');
    expect(payload.currency.code).toBe('EUR');
    expect(await screen.findByText(/Settings saved/)).toBeInTheDocument();
  });

  it('shows the admin-access message when the load is rejected with 403', async () => {
    settingsApi.getSystem.mockRejectedValue({ response: { status: 403 } });
    renderPage();

    expect(
      await screen.findByText('You need admin access to view system settings.')
    ).toBeInTheDocument();
    // Admins still get the editable form so they can retry saving.
    expect(screen.getByLabelText(/^Business Name/)).toBeInTheDocument();
  });
});
