import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import BuyTemplateBanner from '../../components/ecommerce/BuyTemplateBanner';
import { openLemonSqueezyCheckout } from '../../services/lemonSqueezy';

vi.mock('../../services/lemonSqueezy', () => ({
  openLemonSqueezyCheckout: vi.fn(),
}));

describe('BuyTemplateBanner', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the template name, price and both actions', () => {
    render(<BuyTemplateBanner templateName="LuminaCloud" price="$49" />);

    expect(screen.getByText('LuminaCloud')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /buy template.*\$49/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Dismiss banner' })).toBeInTheDocument();
  });

  it('opens checkout with the template metadata', () => {
    render(
      <BuyTemplateBanner
        templateName="LuminaCloud"
        price="$49"
        checkoutUrl="https://example.test/checkout"
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /buy template/i }));

    expect(openLemonSqueezyCheckout).toHaveBeenCalledWith(
      expect.objectContaining({
        checkoutUrl: 'https://example.test/checkout',
        customData: { product: 'LuminaCloud', price: '$49' },
      })
    );
  });

  it('can be dismissed', () => {
    render(<BuyTemplateBanner />);

    fireEvent.click(screen.getByRole('button', { name: 'Dismiss banner' }));

    expect(screen.queryByRole('button', { name: /buy template/i })).toBeNull();
    expect(screen.queryByText('LuminaCloud')).toBeNull();
  });

  it('falls back to the default template and price', () => {
    render(<BuyTemplateBanner />);

    expect(screen.getByText('LuminaCloud')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /buy template.*\$49/i })).toBeInTheDocument();
  });
});
