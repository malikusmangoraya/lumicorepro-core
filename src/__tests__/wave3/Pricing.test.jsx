import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const mocks = vi.hoisted(() => ({
  authState: { isAuthenticated: true },
  formatPrice: vi.fn((value) => `$${Number(value).toFixed(2)}`),
}));

vi.mock('../../context/AppContext', () => ({
  useAppContext: () => ({ isAuthenticated: mocks.authState.isAuthenticated }),
}));

vi.mock('../../hooks/useCurrency', () => ({
  useCurrency: () => ({ formatPrice: mocks.formatPrice }),
}));

vi.mock('../../services/apiConfig', () => ({
  getApiKey: vi.fn(() => 'agent-key-123'),
}));

vi.mock('../../services/api', () => ({
  plansAPI: { list: vi.fn() },
  paymentsAPI: { checkout: vi.fn() },
  subscriptionsAPI: { create: vi.fn() },
}));

import Pricing from '../../pages/Pricing';
import { plansAPI, paymentsAPI, subscriptionsAPI } from '../../services/api';

const plans = [
  {
    id: 'starter',
    name: 'Starter',
    description: 'For solo makers',
    amount: '29',
    interval: 'month',
    creditsGrant: '20',
    features: ['20 AI generations', 'Email support'],
  },
  {
    id: 'studio',
    name: 'Studio',
    description: 'For growing teams',
    amount: '99',
    interval: 'month',
    creditsGrant: '100',
    highlight: true,
    features: ['Custom domains'],
  },
  {
    id: 'studio-yearly',
    name: 'Studio Yearly',
    description: 'Two months free',
    amount: '999',
    interval: 'year',
    creditsGrant: '1200',
    features: ['Priority support'],
  },
  {
    id: 'credits-50',
    name: 'Credit Pack',
    description: 'Extra generations',
    amount: '15',
    interval: 'one_time',
    creditsGrant: '50',
    features: ['Commercial license'],
  },
];

const renderPage = () =>
  render(
    <MemoryRouter initialEntries={['/pricing']}>
      <Pricing />
    </MemoryRouter>
  );

beforeEach(() => {
  vi.clearAllMocks();
  mocks.authState.isAuthenticated = true;
  plansAPI.list.mockResolvedValue({ data: { data: plans } });
  subscriptionsAPI.create.mockResolvedValue({ data: {} });
  paymentsAPI.checkout.mockResolvedValue({ data: {} });
});

describe('Pricing page', () => {
  it('loads plans and renders subscription cards plus one-time credit packs', async () => {
    renderPage();

    expect(screen.getByRole('status', { name: 'Loading...' })).toBeTruthy();
    expect(await screen.findByRole('heading', { name: 'Starter' })).toBeTruthy();

    expect(screen.getByRole('heading', { name: 'Studio' })).toBeTruthy();
    expect(screen.getByRole('heading', { name: 'Studio Yearly' })).toBeTruthy();
    expect(screen.getByText('$29.00')).toBeTruthy();
    expect(screen.getByText('$99.00')).toBeTruthy();
    expect(screen.getByText('$999.00')).toBeTruthy();
    expect(screen.getByText('$15.00')).toBeTruthy();
    expect(screen.getAllByText('/month')).toHaveLength(2);
    expect(screen.getByText('/year')).toBeTruthy();
    expect(screen.getByText('one-time')).toBeTruthy();
    expect(screen.getByText('+20 AI credits / month')).toBeTruthy();
    expect(screen.getByText('50 credits')).toBeTruthy();
    expect(screen.getByText('Most popular')).toBeTruthy();
    expect(screen.getAllByRole('button', { name: /choose plan/i })).toHaveLength(3);
    expect(screen.getAllByRole('button', { name: /buy credits/i })).toHaveLength(1);
  });

  it('asks unauthenticated visitors to log in and disables every checkout CTA', async () => {
    mocks.authState.isAuthenticated = false;
    renderPage();

    await screen.findByRole('heading', { name: 'Starter' });

    expect(screen.getByText('Please log in before choosing a plan.')).toBeTruthy();
    const ctas = screen.getAllByRole('button', { name: /choose plan|buy credits/i });
    expect(ctas).toHaveLength(4);
    for (const cta of ctas) {
      expect(cta).toBeDisabled();
    }
    expect(subscriptionsAPI.create).not.toHaveBeenCalled();
    expect(paymentsAPI.checkout).not.toHaveBeenCalled();
  });

  it('creates a subscription checkout and reports a missing checkout URL', async () => {
    renderPage();
    await screen.findByRole('heading', { name: 'Starter' });

    fireEvent.click(screen.getAllByRole('button', { name: /choose plan/i })[0]);

    await waitFor(() => {
      expect(subscriptionsAPI.create).toHaveBeenCalledWith('starter');
    });
    expect(
      await screen.findByText('Checkout session unavailable — is Stripe configured?')
    ).toBeTruthy();
    expect(paymentsAPI.checkout).not.toHaveBeenCalled();
    expect(screen.getAllByRole('button', { name: /choose plan/i })[0]).toBeEnabled();
  });

  it('sends one-time credit packs through the payments checkout without an agent key', async () => {
    renderPage();
    await screen.findByRole('heading', { name: 'Credit Pack' });

    fireEvent.click(screen.getByRole('button', { name: /buy credits/i }));

    await waitFor(() => {
      expect(paymentsAPI.checkout).toHaveBeenCalledWith({ planId: 'credits-50' });
    });
    // The backend stopped accepting a client-supplied agent credential (it was
    // replayed against the agent credit top-up endpoint), so none may be sent.
    const payload = paymentsAPI.checkout.mock.calls[0][0];
    expect(payload).not.toHaveProperty('agentApiKey');
    expect(subscriptionsAPI.create).not.toHaveBeenCalled();
  });

  it('shows the backend checkout error and re-enables the CTA', async () => {
    subscriptionsAPI.create.mockRejectedValue({
      response: { data: { error: 'Card declined by issuer' } },
    });
    renderPage();
    await screen.findByRole('heading', { name: 'Starter' });

    fireEvent.click(screen.getAllByRole('button', { name: /choose plan/i })[1]);

    expect(await screen.findByText('Card declined by issuer')).toBeTruthy();
    await waitFor(() => {
      expect(screen.getAllByRole('button', { name: /choose plan/i })[1]).toBeEnabled();
    });
  });
});
