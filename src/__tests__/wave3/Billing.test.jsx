import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';

vi.mock('../../hooks/useCurrency', () => ({
  useCurrency: () => ({ formatPrice: (value) => `$${Number(value).toFixed(2)}` }),
}));

vi.mock('../../services/api', () => ({
  subscriptionsAPI: { list: vi.fn(), cancel: vi.fn() },
  paymentsAPI: { portal: vi.fn() },
}));

import Billing from '../../pages/Billing';
import { paymentsAPI, subscriptionsAPI } from '../../services/api';

const activeSub = {
  id: 7,
  planName: 'Pro',
  status: 'active',
  currentPeriodStart: '2026-10-01T00:00:00Z',
  currentPeriodEnd: '2026-11-01T00:00:00Z',
  plan: { amount: '79', interval: 'month' },
};

beforeEach(() => {
  vi.clearAllMocks();
  subscriptionsAPI.list.mockResolvedValue({ data: { data: [activeSub] } });
  subscriptionsAPI.cancel.mockResolvedValue({ data: {} });
  paymentsAPI.portal.mockResolvedValue({ data: {} });
});

describe('Billing page', () => {
  it('renders the active subscription with status, period and price', async () => {
    render(<Billing />);

    expect(await screen.findByText('Pro')).toBeTruthy();
    expect(screen.getByText('active')).toBeTruthy();
    expect(screen.getByText(/Period:/)).toBeTruthy();
    expect(screen.getByText(/\$79\.00\/mo/)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Cancel plan' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Open billing portal' })).toBeEnabled();
  });

  it('shows the empty state with a link to pricing when there is no subscription', async () => {
    subscriptionsAPI.list.mockResolvedValue({ data: { data: [] } });

    render(<Billing />);

    expect(await screen.findByText(/No active subscriptions/)).toBeTruthy();
    expect(screen.getByRole('link', { name: 'Browse plans' })).toHaveAttribute(
      'href',
      '/pricing'
    );
  });

  it('shows a spinner while subscriptions are loading', async () => {
    let resolveList;
    subscriptionsAPI.list.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveList = resolve;
        })
    );

    render(<Billing />);

    expect(screen.getByRole('status', { name: 'Loading...' })).toBeTruthy();

    resolveList({ data: { data: [activeSub] } });

    expect(await screen.findByText('Pro')).toBeTruthy();
    expect(screen.queryByRole('status', { name: 'Loading...' })).toBeNull();
  });

  it('opens the Stripe billing portal and reports an unavailable portal', async () => {
    render(<Billing />);
    await screen.findByText('Pro');

    fireEvent.click(screen.getByRole('button', { name: 'Open billing portal' }));

    await waitFor(() => {
      expect(paymentsAPI.portal).toHaveBeenCalledTimes(1);
    });
    expect(
      await screen.findByText('Billing portal unavailable — is Stripe configured?')
    ).toBeTruthy();
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Open billing portal' })).toBeEnabled();
    });
  });

  it('surfaces the backend error when the portal request fails', async () => {
    paymentsAPI.portal.mockRejectedValue({
      response: { data: { error: 'Stripe portal is not configured' } },
    });
    render(<Billing />);
    await screen.findByText('Pro');

    fireEvent.click(screen.getByRole('button', { name: 'Open billing portal' }));

    expect(await screen.findByText('Stripe portal is not configured')).toBeTruthy();
  });

  it('cancels a subscription, reloads the list and disables the cancelled plan', async () => {
    let listCalls = 0;
    subscriptionsAPI.list.mockImplementation(() => {
      listCalls += 1;
      const data = listCalls === 1 ? [activeSub] : [{ ...activeSub, status: 'canceled' }];
      return Promise.resolve({ data: { data } });
    });

    render(<Billing />);
    await screen.findByText('Pro');

    fireEvent.click(screen.getByRole('button', { name: 'Cancel plan' }));

    await waitFor(() => {
      expect(subscriptionsAPI.cancel).toHaveBeenCalledWith(7);
    });
    expect(
      await screen.findByText('Subscription cancelled — access continues until period end.')
    ).toBeTruthy();
    await waitFor(() => {
      expect(subscriptionsAPI.list).toHaveBeenCalledTimes(2);
    });
    expect(await screen.findByText('canceled')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Cancel plan' })).toBeDisabled();
  });
});
