import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import ProductCard from '../../components/ecommerce/ProductCard';

const product = {
  id: 'p1',
  name: 'Aurora Headphones',
  image: '/images/aurora.webp',
  price: 129.99,
  compareAtPrice: 159.99,
  rating: 4.5,
  reviewCount: 42,
  badge: 'New',
};

afterEach(() => {
  vi.useRealTimers();
});

describe('ProductCard', () => {
  it('renders the name, image, price, discount and rating', () => {
    render(<ProductCard product={product} />);

    expect(screen.getByRole('img', { name: product.name })).toHaveAttribute('src', product.image);
    expect(screen.getByRole('button', { name: product.name })).toBeInTheDocument();
    expect(screen.getByText('$129.99')).toBeInTheDocument();
    expect(screen.getByText('$159.99')).toBeInTheDocument();
    expect(screen.getByText('19% OFF')).toBeInTheDocument();
    expect(screen.getByText('New')).toBeInTheDocument();
    expect(screen.getByRole('img', { name: '4.5 out of 5 stars' })).toBeInTheDocument();
    expect(screen.getByText('4.5 (42)')).toBeInTheDocument();
  });

  it('adds the product with quantity 1 and confirms briefly', () => {
    vi.useFakeTimers();
    const onAddToCart = vi.fn();
    render(<ProductCard product={product} onAddToCart={onAddToCart} />);

    fireEvent.click(screen.getByRole('button', { name: 'Add' }));

    expect(onAddToCart).toHaveBeenCalledWith({ ...product, quantity: 1 });
    expect(screen.getByRole('button', { name: 'Added' })).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(1500);
    });
    expect(screen.getByRole('button', { name: 'Add' })).toBeInTheDocument();
  });

  it('invokes the wishlist and view callbacks with the product', () => {
    const onToggleWishlist = vi.fn();
    const onView = vi.fn();
    render(
      <ProductCard product={product} onToggleWishlist={onToggleWishlist} onView={onView} />
    );

    fireEvent.click(screen.getByRole('button', { name: `Add ${product.name} to wishlist` }));
    expect(onToggleWishlist).toHaveBeenCalledWith(product);

    fireEvent.click(screen.getByRole('button', { name: `View ${product.name}` }));
    fireEvent.click(screen.getByRole('button', { name: product.name }));
    expect(onView).toHaveBeenCalledTimes(2);
    expect(onView).toHaveBeenNthCalledWith(1, product);
    expect(onView).toHaveBeenNthCalledWith(2, product);
  });

  it('adds the quantity chosen in the withQty variant', () => {
    vi.useFakeTimers();
    const onAddToCart = vi.fn();
    render(<ProductCard product={product} onAddToCart={onAddToCart} variant="withQty" />);

    const increase = screen.getByRole('button', { name: 'Increase quantity' });
    fireEvent.click(increase);
    fireEvent.click(increase);
    expect(screen.getByLabelText('Quantity')).toHaveValue(3);

    fireEvent.click(screen.getByRole('button', { name: 'Add' }));
    expect(onAddToCart).toHaveBeenCalledWith(expect.objectContaining({ id: 'p1', quantity: 3 }));

    act(() => {
      vi.advanceTimersByTime(1500);
    });
  });

  it('omits cart and wishlist actions when callbacks are absent', () => {
    render(<ProductCard product={product} />);

    expect(screen.queryByRole('button', { name: 'Add' })).toBeNull();
    expect(screen.queryByRole('button', { name: /wishlist/i })).toBeNull();
  });

  it('falls back to defaults for a missing product and honours the currency prop', () => {
    render(<ProductCard product={null} currency="EUR" />);

    expect(screen.getByText('Untitled product')).toBeInTheDocument();
    expect(screen.getByText('€0.00')).toBeInTheDocument();
    expect(screen.getByRole('img', { name: '4.5 out of 5 stars' })).toBeInTheDocument();
  });
});
