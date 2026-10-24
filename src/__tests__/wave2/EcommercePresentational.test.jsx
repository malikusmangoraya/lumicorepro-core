import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import RatingStars from '../../components/ecommerce/RatingStars';
import DiscountBadge from '../../components/ecommerce/DiscountBadge';
import ProductGrid from '../../components/ecommerce/ProductGrid';

afterEach(() => {
  vi.useRealTimers();
});

describe('RatingStars', () => {
  it('exposes the rating as an accessible image with a title', () => {
    render(<RatingStars rating={4.5} />);

    const rating = screen.getByRole('img', { name: '4.5 out of 5 stars' });
    expect(rating).toHaveAttribute('title', '4.5 out of 5 stars');
  });

  it('shows the numeric value and review count when requested', () => {
    render(<RatingStars rating={4.5} reviewCount={12} showValue />);

    expect(screen.getByText('4.5 (12)')).toBeInTheDocument();
  });

  it('supports a custom maximum and hides a zero review count', () => {
    render(<RatingStars rating={3} max={10} showValue />);

    expect(screen.getByRole('img', { name: '3 out of 10 stars' })).toBeInTheDocument();
    expect(screen.getByText('3.0')).toBeInTheDocument();
    expect(screen.queryByText(/\(0\)/)).toBeNull();
  });
});

describe('DiscountBadge', () => {
  it('renders an explicit percentage', () => {
    render(<DiscountBadge discountPercent={25} />);

    expect(screen.getByText('25% OFF')).toBeInTheDocument();
  });

  // Finding (bug): discountPercent defaults to 0, and Number.isFinite(0) is
  // true, so the compareAtPrice/price fallback can never run.
  it('derives the discount from compareAtPrice when no percentage is passed', () => {
    const { container } = render(<DiscountBadge compareAtPrice={200} price={150} />);

    // 25% off — the old implementation treated the default 0 as an explicit
    // percentage and rendered nothing.
    expect(container.textContent).toMatch(/25/);
  });

  it('prefers an explicit percentage and custom label', () => {
    render(<DiscountBadge discountPercent={40} label="Flash sale" />);

    expect(screen.getByText('Flash sale')).toBeInTheDocument();
  });

  it('renders nothing when there is no discount', () => {
    const { container } = render(<DiscountBadge compareAtPrice={0} price={50} />);

    expect(container).toBeEmptyDOMElement();
  });
});

describe('ProductGrid', () => {
  const products = [
    { id: 'a', name: 'Alpha Lamp', price: 20, rating: 4 },
    { id: 'b', name: 'Beta Chair', price: 80, rating: 5 },
  ];

  it('renders provided products with title and subtitle', () => {
    render(<ProductGrid products={products} title="Featured" subtitle="Handpicked for you" />);

    expect(screen.getByRole('heading', { name: 'Featured' })).toBeInTheDocument();
    expect(screen.getByText('Handpicked for you')).toBeInTheDocument();
    expect(screen.getAllByRole('article')).toHaveLength(2);
    expect(screen.getByText('Alpha Lamp')).toBeInTheDocument();
    expect(screen.getByText('Beta Chair')).toBeInTheDocument();
  });

  it('forwards interaction callbacks to the cards', () => {
    vi.useFakeTimers();
    const onAddToCart = vi.fn();
    render(<ProductGrid products={products} onAddToCart={onAddToCart} />);

    fireEvent.click(screen.getAllByRole('button', { name: 'Add' })[0]);

    expect(onAddToCart).toHaveBeenCalledWith(expect.objectContaining({ id: 'a', quantity: 1 }));

    act(() => {
      vi.advanceTimersByTime(1500);
    });
  });

  it('falls back to eight demo cards when the list is empty', () => {
    render(<ProductGrid products={[]} />);

    expect(screen.getAllByRole('article')).toHaveLength(8);
    expect(screen.getAllByText('Premium product')).toHaveLength(8);
  });
});
