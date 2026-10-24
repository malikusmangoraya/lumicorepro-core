import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import CartEmpty from '../../components/ecommerce/CartEmpty';

describe('CartEmpty', () => {
  it('renders the empty-state heading and copy', () => {
    render(<CartEmpty />);

    expect(screen.getByRole('heading', { name: 'Your cart is empty' })).toBeInTheDocument();
    expect(screen.getByText(/added anything yet/i)).toBeInTheDocument();
    expect(screen.queryByRole('button')).toBeNull();
  });

  it('calls onBrowse from the CTA', () => {
    const onBrowse = vi.fn();
    render(<CartEmpty onBrowse={onBrowse} />);

    fireEvent.click(screen.getByRole('button', { name: /browse products/i }));

    expect(onBrowse).toHaveBeenCalledOnce();
  });

  it('supports custom copy and CTA label', () => {
    render(
      <CartEmpty
        title="Nothing here"
        subtitle="Add a template to get started"
        browseLabel="Explore templates"
        onBrowse={vi.fn()}
      />
    );

    expect(screen.getByRole('heading', { name: 'Nothing here' })).toBeInTheDocument();
    expect(screen.getByText('Add a template to get started')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Explore templates' })).toBeInTheDocument();
  });

  it('hides the CTA when no handler is supplied', () => {
    render(<CartEmpty browseLabel="Browse products" />);

    expect(screen.queryByRole('button', { name: /browse/i })).toBeNull();
  });
});
