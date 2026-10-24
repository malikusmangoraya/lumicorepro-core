import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import PricingTable from '../../components/ecommerce/PricingTable';
import { openLemonSqueezyCheckout } from '../../services/lemonSqueezy';

vi.mock('../../services/lemonSqueezy', () => ({
  openLemonSqueezyCheckout: vi.fn(),
}));

describe('PricingTable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the three plans with monthly prices by default', () => {
    render(<PricingTable />);

    expect(
      screen.getByRole('heading', { name: 'Flexible, Transparent Pricing' })
    ).toBeInTheDocument();
    for (const plan of ['Starter', 'Pro', 'Enterprise']) {
      expect(screen.getByRole('heading', { name: plan })).toBeInTheDocument();
    }
    expect(screen.getByText('$29')).toBeInTheDocument();
    expect(screen.getByText('$79')).toBeInTheDocument();
    expect(screen.getByText('$199')).toBeInTheDocument();
    expect(screen.getAllByText('/ month')).toHaveLength(3);
  });

  it('switches to annual pricing with the billing toggle', () => {
    render(<PricingTable />);
    const toggle = screen.getByRole('switch');

    expect(toggle).toHaveAttribute('aria-checked', 'false');
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute('aria-checked', 'true');
    expect(screen.getByText('$24')).toBeInTheDocument();
    expect(screen.queryByText('$29')).toBeNull();
    expect(screen.getAllByText('/ mo, billed annually')).toHaveLength(3);
  });

  it('opens monthly checkout with the plan variant id', () => {
    render(<PricingTable />);

    fireEvent.click(screen.getAllByRole('button', { name: /buy on lemon squeezy/i })[0]);

    expect(openLemonSqueezyCheckout).toHaveBeenCalledWith({
      customData: {
        planName: 'Starter',
        billingCycle: 'monthly',
        amount: 29,
        variantId: 'starter_monthly',
      },
      onSuccess: expect.any(Function),
    });
  });

  it('opens annual checkout with the yearly amount for the selected plan', () => {
    render(<PricingTable />);

    fireEvent.click(screen.getByRole('switch'));
    fireEvent.click(screen.getAllByRole('button', { name: /buy on lemon squeezy/i })[1]);

    expect(openLemonSqueezyCheckout).toHaveBeenCalledWith(
      expect.objectContaining({
        customData: {
          planName: 'Pro',
          billingCycle: 'annual',
          amount: 768,
          variantId: 'pro_annual',
        },
      })
    );
  });

  it('supports custom title and subtitle copy', () => {
    render(<PricingTable title="Pick a plan" subtitle="Simple pricing" />);

    expect(screen.getByRole('heading', { name: 'Pick a plan' })).toBeInTheDocument();
    expect(screen.getByText('Simple pricing')).toBeInTheDocument();
  });
});
