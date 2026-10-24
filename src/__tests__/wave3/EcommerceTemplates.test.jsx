import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import ProductListing from '../../templates/ecommerce/ProductListing';
import ProductDetails from '../../templates/ecommerce/ProductDetails';
import ShoppingCart from '../../templates/ecommerce/ShoppingCart';
import Checkout from '../../templates/ecommerce/Checkout';
import OrdersHistory from '../../templates/ecommerce/OrdersHistory';

/**
 * The template pages are presentational: they render local mock data and need
 * only a router (TemplateShell renders a "Templates" back link).
 */
function renderTemplate(ui) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe('ProductListing template', () => {
  it('renders the header, stats, features, and all seeded products', () => {
    renderTemplate(<ProductListing />);

    expect(screen.getByRole('heading', { level: 1, name: 'Product Listing' })).toBeInTheDocument();
    expect(
      screen.getByText('Browse, filter, and sort products with enhanced UI.')
    ).toBeInTheDocument();

    for (const stat of ['Total Products', 'Categories', 'Avg Rating', 'In Stock']) {
      // "Categories" also labels the sidebar filter, so allow duplicates.
      expect(screen.getAllByText(stat).length).toBeGreaterThan(0);
    }

    expect(screen.getByRole('heading', { name: 'Why Shop With Us' })).toBeInTheDocument();
    for (const feature of ['Free Shipping', 'Secure Payment', 'Easy Returns', '24/7 Support']) {
      expect(screen.getByText(feature)).toBeInTheDocument();
    }

    for (const name of [
      'Nova UI Kit',
      'Pulse Dashboard',
      'Chat Starter',
      'Commerce Pack',
      'Insight Charts',
      'Prompt Lab',
    ]) {
      expect(screen.getByText(name)).toBeInTheDocument();
    }
    expect(screen.getAllByRole('img')).toHaveLength(6);
    expect(screen.getByAltText('Nova UI Kit')).toBeInTheDocument();
    expect(screen.getByText('$129')).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: 'Sort products' })).toBeInTheDocument();
  });

  it('filters products by search text after the debounce', async () => {
    renderTemplate(<ProductListing />);

    fireEvent.change(screen.getByPlaceholderText(/search products/i), {
      target: { value: 'pulse' },
    });

    await waitFor(() => {
      expect(screen.queryByText('Nova UI Kit')).toBeNull();
    });

    expect(screen.getByText('Pulse Dashboard')).toBeInTheDocument();
    expect(screen.getByAltText('Pulse Dashboard')).toBeInTheDocument();
    expect(screen.queryByText('Chat Starter')).toBeNull();
  });

  it('filters products by category', () => {
    const { container } = renderTemplate(<ProductListing />);

    const categoryNav = container.querySelector('aside');
    expect(categoryNav).not.toBeNull();

    fireEvent.click(within(categoryNav).getByRole('button', { name: 'Dashboards' }));

    expect(screen.getByText('Pulse Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Insight Charts')).toBeInTheDocument();
    expect(screen.queryByText('Nova UI Kit')).toBeNull();
    expect(screen.queryByText('Prompt Lab')).toBeNull();
  });

  it('shows the empty state when no product matches', async () => {
    renderTemplate(<ProductListing />);

    fireEvent.change(screen.getByPlaceholderText(/search products/i), {
      target: { value: 'no-such-product' },
    });

    await waitFor(() => {
      expect(screen.getByText('No products found')).toBeInTheDocument();
    });
    expect(screen.getByText('Try adjusting your search or filters')).toBeInTheDocument();
  });
});

describe('ProductDetails template', () => {
  it('renders the product gallery copy, price, and purchase controls', () => {
    renderTemplate(<ProductDetails />);

    expect(screen.getByRole('heading', { level: 1, name: 'Product Details' })).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { level: 2, name: 'Pulse Dashboard Kit' })
    ).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('$129')).toBeInTheDocument();
    expect(screen.getByText(/4\.9 · 128 reviews/)).toBeInTheDocument();
    expect(
      screen.getByText(
        'A calm, professional dashboard kit with charts, tables, and settings patterns.'
      )
    ).toBeInTheDocument();

    for (const size of ['S', 'M', 'L', 'XL']) {
      expect(screen.getByRole('button', { name: size })).toBeInTheDocument();
    }
    expect(screen.getByRole('button', { name: 'Add to cart' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Wishlist' })).toBeInTheDocument();
  });

  it('increments the quantity and never drops below one', () => {
    renderTemplate(<ProductDetails />);

    const decrement = screen.getByRole('button', { name: '-' });
    const increment = screen.getByRole('button', { name: '+' });

    fireEvent.click(increment);
    expect(screen.getByText('2')).toBeInTheDocument();

    fireEvent.click(decrement);
    expect(screen.getByText('1')).toBeInTheDocument();

    fireEvent.click(decrement);
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('marks the selected size as active', () => {
    renderTemplate(<ProductDetails />);

    const small = screen.getByRole('button', { name: 'S' });
    const medium = screen.getByRole('button', { name: 'M' });
    expect(small).toHaveClass('bg-primary');
    expect(medium).not.toHaveClass('bg-primary');

    fireEvent.click(medium);

    expect(medium).toHaveClass('bg-primary');
    expect(small).not.toHaveClass('bg-primary');
  });
});

describe('ShoppingCart template', () => {
  it('renders the seeded items and a matching order summary', () => {
    renderTemplate(<ShoppingCart />);

    expect(screen.getByRole('heading', { level: 1, name: 'Shopping Cart' })).toBeInTheDocument();
    expect(screen.getByText('Nova UI Kit')).toBeInTheDocument();
    expect(screen.getByText('Chat Starter')).toBeInTheDocument();
    expect(screen.getByText('$79')).toBeInTheDocument();
    expect(screen.getByText('$49')).toBeInTheDocument();

    // 79 * 1 + 49 * 2 = 177, plus 8 shipping = 185.
    expect(screen.getByText('$177.00')).toBeInTheDocument();
    expect(screen.getByText('$8.00')).toBeInTheDocument();
    expect(screen.getByText('$185.00')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Coupon code')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Checkout' })).toBeInTheDocument();
  });

  it('increments a line quantity and recalculates the totals', () => {
    renderTemplate(<ShoppingCart />);

    fireEvent.click(screen.getAllByRole('button', { name: '+' })[0]);

    // Nova UI Kit now has qty 2: 79 * 2 + 49 * 2 = 256, plus 8 shipping = 264.
    expect(screen.getByText('$256.00')).toBeInTheDocument();
    expect(screen.getByText('$264.00')).toBeInTheDocument();
  });

  it('removes a line item and recalculates the totals', () => {
    renderTemplate(<ShoppingCart />);

    fireEvent.click(screen.getAllByRole('button', { name: 'Remove' })[0]);

    expect(screen.queryByText('Nova UI Kit')).toBeNull();
    expect(screen.getByText('Chat Starter')).toBeInTheDocument();
    expect(screen.getByText('$98.00')).toBeInTheDocument();
    expect(screen.getByText('$106.00')).toBeInTheDocument();
  });

  it('shows the empty state after every item is removed', () => {
    renderTemplate(<ShoppingCart />);

    fireEvent.click(screen.getAllByRole('button', { name: 'Remove' })[0]);
    fireEvent.click(screen.getByRole('button', { name: 'Remove' }));

    expect(screen.getByText('Cart is empty')).toBeInTheDocument();
    expect(screen.getByText('Add products to continue.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Browse products' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Summary' })).toBeNull();
  });
});

describe('Checkout template', () => {
  it('starts on the shipping step with progress and a disabled back button', () => {
    renderTemplate(<Checkout />);

    expect(screen.getByRole('heading', { level: 1, name: 'Checkout' })).toBeInTheDocument();

    const progress = screen.getByRole('progressbar', { name: 'Shipping' });
    expect(progress).toHaveAttribute('aria-valuenow', '25');

    expect(screen.getByLabelText('Full name')).toBeInTheDocument();
    expect(screen.getByLabelText('Address')).toBeInTheDocument();
    expect(screen.getByLabelText('City')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Back' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Continue' })).toBeInTheDocument();
  });

  it('advances to payment and returns to shipping', () => {
    renderTemplate(<Checkout />);

    fireEvent.click(screen.getByRole('button', { name: 'Continue' }));

    expect(screen.getByRole('progressbar', { name: 'Payment' })).toHaveAttribute(
      'aria-valuenow',
      '50'
    );
    expect(screen.getByLabelText('Card number')).toBeInTheDocument();
    expect(screen.getByLabelText('Expiry')).toBeInTheDocument();
    expect(screen.getByLabelText('CVC')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Back' }));

    expect(screen.getByRole('progressbar', { name: 'Shipping' })).toBeInTheDocument();
    expect(screen.getByLabelText('Full name')).toBeInTheDocument();
  });

  it('reviews the order, places it, and reaches the confirmation step', () => {
    renderTemplate(<Checkout />);

    fireEvent.click(screen.getByRole('button', { name: 'Continue' }));
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }));

    expect(screen.getByRole('progressbar', { name: 'Review' })).toHaveAttribute(
      'aria-valuenow',
      '75'
    );
    expect(screen.getByText('Order total: $97.00')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Place order' }));

    expect(screen.getByText('Order placed')).toBeInTheDocument();
    expect(screen.getByText('Confirmation sent to your email.')).toBeInTheDocument();
    expect(screen.getByRole('progressbar', { name: 'Done' })).toHaveAttribute(
      'aria-valuenow',
      '100'
    );
    expect(screen.getByRole('button', { name: 'Done' })).toBeInTheDocument();
  });
});

describe('OrdersHistory template', () => {
  it('lists every order with its filters and totals', () => {
    renderTemplate(<OrdersHistory />);

    expect(screen.getByRole('heading', { level: 1, name: 'Orders History' })).toBeInTheDocument();

    for (const filter of ['All', 'Pending', 'Shipped', 'Delivered']) {
      expect(screen.getByRole('button', { name: filter })).toBeInTheDocument();
    }

    for (const order of ['ORD-1042', 'ORD-1048', 'ORD-1051']) {
      expect(screen.getByText(order)).toBeInTheDocument();
    }
    expect(screen.getByText('$128')).toBeInTheDocument();
    expect(screen.getByText('$79')).toBeInTheDocument();
    expect(screen.getByText('$214')).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Details' })).toHaveLength(3);
  });

  it('filters down to shipped orders and back to all orders', () => {
    renderTemplate(<OrdersHistory />);

    fireEvent.click(screen.getByRole('button', { name: 'Shipped' }));

    expect(screen.getByText('ORD-1048')).toBeInTheDocument();
    expect(screen.queryByText('ORD-1042')).toBeNull();
    expect(screen.queryByText('ORD-1051')).toBeNull();
    expect(screen.getByText('shipped')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'All' }));

    expect(screen.getByText('ORD-1042')).toBeInTheDocument();
    expect(screen.getByText('ORD-1048')).toBeInTheDocument();
    expect(screen.getByText('ORD-1051')).toBeInTheDocument();
  });

  it('filters down to pending orders', () => {
    renderTemplate(<OrdersHistory />);

    fireEvent.click(screen.getByRole('button', { name: 'Pending' }));

    expect(screen.getByText('ORD-1051')).toBeInTheDocument();
    expect(screen.queryByText('ORD-1042')).toBeNull();
    expect(screen.queryByText('ORD-1048')).toBeNull();
    expect(screen.getByText('pending')).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Details' })).toHaveLength(1);
  });
});
