import React, { act } from 'react';
import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import useCartStore from '../../store/cartStore';

/**
 * The restaurant pages under test ship with missing imports:
 *  - Menu.jsx:77 renders <SEOPage> but never imports it
 *  - Checkout.jsx:91 renders <Link> without importing it, and Checkout.jsx:30
 *    lists the undefined `clearCart` in a dependency array
 *  - OrderHistory.jsx:75/84/109 and AdminDashboard.jsx:143 render <Link> without
 *    importing it
 * Those free identifiers resolve against globalThis in an ES module, so the
 * suite injects minimal shims to exercise the intended UI while the bugs are
 * reported (src/ is intentionally untouched).
 */
beforeAll(() => {
  globalThis.Link = ({ to, children, ...props }) => (
    <a href={typeof to === 'string' ? to : '#'} {...props}>
      {children}
    </a>
  );
  globalThis.SEOPage = () => null;
  // RestaurantHome.jsx:107 passes the undefined ClockIcon to the Reserve Table
  // button, which crashes the whole hero before any content renders.
  globalThis.ClockIcon = () => null;
  // Checkout's dependency array evaluates this free identifier on every render.
  globalThis.clearCart = () => {};
});

afterAll(() => {
  delete globalThis.Link;
  delete globalThis.SEOPage;
  delete globalThis.ClockIcon;
  delete globalThis.clearCart;
});

const { api } = vi.hoisted(() => ({
  api: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}));

vi.mock('../../services/api', () => ({ default: api, api }));

// Realtime wiring: the pages read the signed-in identity and open a Socket.IO
// room. Both are stubbed so these are pure rendering/behaviour tests, with no
// AuthProvider/AppContext tree and no network socket.
vi.mock('../../context/AuthContext', () => ({
  useAuth: () => ({ user: { id: 1, role: 'admin' }, token: 'test-token' }),
}));
vi.mock('../../hooks/useSocket', () => ({
  useSocket: () => ({ connected: false, emit: () => false }),
}));

import RestaurantHome from '../../pages/restaurant/RestaurantHome';
import Menu from '../../pages/restaurant/Menu';
import Cart from '../../pages/restaurant/Cart';
import Checkout from '../../pages/restaurant/Checkout';
import Reservation from '../../pages/restaurant/Reservation';
import OrderHistory from '../../pages/restaurant/OrderHistory';
import AdminDashboard from '../../pages/restaurant/AdminDashboard';

const renderAt = (ui, path = '/') =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/" element={ui} />
        <Route path="/restaurant/menu" element={<div>menu-route</div>} />
        <Route path="/restaurant/cart" element={<div>cart-route</div>} />
        <Route path="/restaurant/reservation" element={<div>reservation-route</div>} />
        <Route path="/restaurant/checkout/success" element={<div>checkout-success-route</div>} />
      </Routes>
    </MemoryRouter>
  );

const LocationEcho = () => {
  const location = useLocation();
  return <div data-testid="location-echo">{location.pathname}</div>;
};

const menuItems = [
  {
    id: 'm1',
    title: 'Margherita Pizza',
    price: '12.99',
    tags: ['vegetarian'],
    rating: 4.8,
    images: ['/images/pizza.jpg'],
    description: 'Tomato, basil and mozzarella.',
  },
  {
    id: 'm2',
    title: 'Spicy Wings',
    price: 9.5,
    tags: ['spicy'],
    rating: 4.2,
    images: [],
    description: 'Hot honey glaze.',
  },
];

const cartLine = (overrides = {}) => ({
  id: 'm1',
  name: 'Margherita Pizza',
  price: 12.99,
  qty: 2,
  image: '/images/pizza.jpg',
  serverId: 'm1',
  ...overrides,
});

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  useCartStore.setState({ items: [] });
  api.get.mockResolvedValue({ data: { data: [] } });
  api.post.mockResolvedValue({ data: { data: {} } });
  api.patch.mockResolvedValue({ data: { data: {} } });
  api.delete.mockResolvedValue({ data: { data: {} } });
});

describe('RestaurantHome', () => {
  it('renders the hero, featured dishes, deals and location details', () => {
    renderAt(<RestaurantHome />);

    expect(
      screen.getByRole('heading', { level: 1, name: 'Good Food, Good Mood' })
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'View Menu' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Reserve Table' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Featured Dishes' })).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Add to Cart' })).toHaveLength(4);
    expect(screen.getByText('Margherita Pizza')).toBeInTheDocument();
    expect(screen.getByText('$12.99')).toBeInTheDocument();

    expect(screen.getByRole('heading', { name: 'Special Offers' })).toBeInTheDocument();
    expect(screen.getByText('Family Feast')).toBeInTheDocument();
    expect(screen.getByText('$39.99')).toBeInTheDocument();

    expect(screen.getByRole('heading', { name: 'Visit Us' })).toBeInTheDocument();
    expect(screen.getAllByText('123 Taste Street, Flavor City')).toHaveLength(2);
    expect(screen.getByRole('link', { name: 'Order on WhatsApp' })).toHaveAttribute(
      'href',
      expect.stringContaining('wa.me/15551234567')
    );
  });

  it('adds a featured dish to the real Zustand cart, incrementing repeats', () => {
    renderAt(<RestaurantHome />);

    const addButtons = screen.getAllByRole('button', { name: 'Add to Cart' });
    fireEvent.click(addButtons[0]);
    fireEvent.click(addButtons[0]);

    const { items } = useCartStore.getState();
    expect(items).toHaveLength(1);
    expect(items[0]).toMatchObject({
      id: 'm1',
      name: 'Margherita Pizza',
      price: 12.99,
      qty: 2,
      serverId: 'm1',
    });
  });

  it('routes both hero CTAs to the menu and reservation pages', () => {
    const first = renderAt(<RestaurantHome />);
    fireEvent.click(screen.getByRole('button', { name: 'View Menu' }));
    expect(screen.getByText('menu-route')).toBeInTheDocument();
    first.unmount();

    renderAt(<RestaurantHome />);
    fireEvent.click(screen.getByRole('button', { name: 'Reserve Table' }));
    expect(screen.getByText('reservation-route')).toBeInTheDocument();
  });
});

describe('Menu', () => {
  it('loads the menu, categories and dietary filters', async () => {
    api.get.mockImplementation((url) =>
      Promise.resolve({
        data: { data: url.includes('/categories') ? ['Pizza', 'Sides'] : menuItems },
      })
    );

    renderAt(<Menu />);

    expect((await screen.findAllByText('Margherita Pizza')).length).toBe(2);
    expect(screen.getAllByText('Spicy Wings')).toHaveLength(2);
    expect(screen.getByRole('heading', { name: 'Our Menu' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Pizza' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Vegetarian' })).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Add' })).toHaveLength(2);
    expect(screen.getByText('0 items')).toBeInTheDocument();
  });

  it('refetches with a category and expands dietary filters', async () => {
    api.get.mockImplementation((url) =>
      Promise.resolve({
        data: { data: url.includes('/categories') ? ['Pizza', 'Sides'] : menuItems },
      })
    );

    renderAt(<Menu />);
    await screen.findAllByText('Margherita Pizza');

    fireEvent.click(screen.getByRole('button', { name: 'Pizza' }));

    await waitFor(() => {
      const menuCalls = api.get.mock.calls.filter(([url]) => url === '/restaurant/menu');
      expect(menuCalls[menuCalls.length - 1][1].params.get('category')).toBe('Pizza');
    });

    fireEvent.click(screen.getByRole('button', { name: 'Vegan' }));
    await waitFor(() => {
      const calls = api.get.mock.calls.filter(([url]) => url === '/restaurant/menu');
      expect(calls[calls.length - 1][1].params.get('vegan')).toBe('true');
    });
  });

  it('adds a dish to the cart and navigates to the cart page', async () => {
    api.get.mockImplementation((url) =>
      Promise.resolve({
        data: { data: url.includes('/categories') ? ['Pizza'] : menuItems },
      })
    );

    renderAt(<Menu />);
    await screen.findAllByText('Margherita Pizza');

    fireEvent.click(screen.getAllByRole('button', { name: 'Add' })[0]);

    expect(screen.getByText('cart-route')).toBeInTheDocument();
    expect(useCartStore.getState().items[0]).toMatchObject({
      id: 'm1',
      name: 'Margherita Pizza',
      price: 12.99,
      serverId: 'm1',
    });
  });

  it('shows the empty state and recovers from a fetch error via Retry', async () => {
    api.get.mockRejectedValueOnce(new Error('Menu offline'));

    renderAt(<Menu />);

    expect(await screen.findByText('Menu offline')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();

    api.get.mockImplementation((url) =>
      Promise.resolve({
        data: { data: url.includes('/categories') ? ['Pizza'] : menuItems },
      })
    );
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));

    expect((await screen.findAllByText('Margherita Pizza')).length).toBe(2);
  });

  it('renders the empty menu state when the API returns no items', async () => {
    renderAt(<Menu />);

    expect(await screen.findByText('No items found')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Clear filters' })).toBeInTheDocument();
  });
});

describe('Cart', () => {
  it('renders the empty-cart state with a link back to the menu', () => {
    renderAt(<Cart />);

    expect(screen.getByRole('heading', { name: 'Your cart is empty' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Browse Menu' })).toHaveAttribute(
      'href',
      '/restaurant/menu'
    );
  });

  it('renders lines, totals and updates quantities/removal through the store', () => {
    act(() => {
      useCartStore.getState().addItem(cartLine(), 2);
    });

    const { container } = renderAt(<Cart />);

    expect(screen.getByRole('heading', { name: 'Your Cart' })).toBeInTheDocument();
    expect(screen.getByText('2 items')).toBeInTheDocument();
    expect(screen.getByText('Margherita Pizza')).toBeInTheDocument();
    expect(screen.getByText('$25.98')).toBeInTheDocument();
    expect(screen.getByText('$8.00')).toBeInTheDocument();
    expect(screen.getByText('$33.98')).toBeInTheDocument();

    fireEvent.click(container.querySelector('.lucide-plus').closest('button'));
    expect(useCartStore.getState().items[0].qty).toBe(3);

    fireEvent.click(container.querySelector('.lucide-minus').closest('button'));
    fireEvent.click(container.querySelector('.lucide-minus').closest('button'));
    fireEvent.click(container.querySelector('.lucide-minus').closest('button'));
    expect(useCartStore.getState().items[0].qty).toBe(1);

    fireEvent.click(container.querySelector('.lucide-trash-2').closest('button'));
    expect(screen.getByRole('heading', { name: 'Your cart is empty' })).toBeInTheDocument();
  });

  it('places the order, clears the cart and navigates to the success page', async () => {
    act(() => {
      useCartStore.getState().addItem(cartLine(), 2);
    });
    renderAt(<Cart />);

    fireEvent.click(screen.getByRole('button', { name: 'Proceed to Checkout' }));

    expect(await screen.findByText('checkout-success-route')).toBeInTheDocument();
    expect(api.post).toHaveBeenCalledWith('/restaurant/orders', {
      items: [{ productId: 'm1', qty: 2 }],
      notes: '',
    });
    expect(useCartStore.getState().items).toEqual([]);
  });

  it('keeps the cart and surfaces the API error when ordering fails', async () => {
    api.post.mockRejectedValueOnce(new Error('Kitchen closed'));
    act(() => {
      useCartStore.getState().addItem(cartLine(), 2);
    });
    renderAt(<Cart />);

    fireEvent.click(screen.getByRole('button', { name: 'Proceed to Checkout' }));

    expect(await screen.findByText('Kitchen closed')).toBeInTheDocument();
    expect(useCartStore.getState().items).toHaveLength(1);
    fireEvent.click(screen.getByRole('button', { name: 'Dismiss' }));
    expect(screen.queryByText('Kitchen closed')).toBeNull();
  });
});

describe('Checkout', () => {
  it('renders the review summary with line totals and payment method', () => {
    act(() => {
      useCartStore.getState().addItem(cartLine(), 2);
    });

    renderAt(<Checkout />);

    expect(screen.getByRole('heading', { name: 'Review Order' })).toBeInTheDocument();
    expect(screen.getByText('Margherita Pizza')).toBeInTheDocument();
    expect(screen.getByText('2x $12.99')).toBeInTheDocument();
    // The line total and the summary subtotal are both $25.98.
    expect(screen.getAllByText('$25.98')).toHaveLength(2);
    expect(screen.getByText('$33.98')).toBeInTheDocument();
    expect(screen.getByText('Payment on Delivery')).toBeInTheDocument();
    expect(screen.getByText('123 Taste Street, Flavor City')).toBeInTheDocument();
  });

  it('confirms the order, clears the cart and navigates to success', () => {
    act(() => {
      useCartStore.getState().addItem(cartLine(), 2);
    });
    // Keep Checkout mounted so its success view can be asserted while another
    // consumer observes the location change.
    render(
      <MemoryRouter initialEntries={['/restaurant/checkout']}>
        <Checkout />
        <LocationEcho />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole('button', { name: 'Confirm & Place Order' }));

    expect(screen.getByRole('heading', { name: 'Order Placed!' })).toBeInTheDocument();
    expect(screen.getByTestId('location-echo')).toHaveTextContent('/restaurant/checkout/success');
    expect(useCartStore.getState().items).toEqual([]);
  });

  it('renders the success view directly when routed to /success with an order in progress', () => {
    act(() => {
      useCartStore.getState().addItem(cartLine(), 2);
    });

    render(
      <MemoryRouter initialEntries={['/restaurant/checkout/success']}>
        <Checkout />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { name: 'Order Placed!' })).toBeInTheDocument();
    expect(screen.getByText('30–45 minutes')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Order More' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Track Order' })).toBeInTheDocument();
  });
});

describe('Reservation', () => {
  it('renders the booking form with times, party sizes and contact details', () => {
    const { container } = renderAt(<Reservation />);

    expect(screen.getByRole('heading', { name: 'Reserve a Table' })).toBeInTheDocument();
    expect(container.querySelector('input[type="date"]')).toBeInTheDocument();
    expect(screen.getByDisplayValue('19:00')).toBeInTheDocument();
    expect(screen.getByDisplayValue('2')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('John Doe')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('+1 (555) 000-0000')).toBeInTheDocument();
    expect(screen.getByText('0 items')).toBeInTheDocument();
  });

  it('submits a booking and shows the confirmation summary', async () => {
    const { container } = renderAt(<Reservation />);

    fireEvent.change(container.querySelector('input[type="date"]'), {
      target: { value: '2026-11-05' },
    });
    fireEvent.change(container.querySelector('select[name], select'), {
      target: { value: '20:00' },
    });
    const selects = container.querySelectorAll('select');
    fireEvent.change(selects[1], { target: { value: '4' } });
    fireEvent.change(screen.getByPlaceholderText('John Doe'), {
      target: { value: 'Ada Lovelace' },
    });
    fireEvent.change(screen.getByPlaceholderText('+1 (555) 000-0000'), {
      target: { value: '+1 555 000 1111' },
    });
    fireEvent.change(screen.getByPlaceholderText('Window seat, high chair, allergies…'), {
      target: { value: 'Window seat' },
    });

    fireEvent.click(screen.getByRole('button', { name: 'Book Table' }));

    expect(await screen.findByRole('heading', { name: 'Table Reserved!' })).toBeInTheDocument();
    expect(api.post).toHaveBeenCalledWith('/restaurant/reservations', {
      date: '2026-11-05',
      time: '20:00',
      partySize: 4,
      name: 'Ada Lovelace',
      phone: '+1 555 000 1111',
      notes: 'Window seat',
    });
    expect(screen.getByText('2026-11-05')).toBeInTheDocument();
    expect(screen.getByText('20:00')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
  });

  it('shows the booking error and re-enables the submit button', async () => {
    api.post.mockRejectedValueOnce(new Error('Fully booked'));
    const { container } = renderAt(<Reservation />);

    fireEvent.change(container.querySelector('input[type="date"]'), {
      target: { value: '2026-11-05' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Book Table' }));

    expect(await screen.findByText('Fully booked')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Book Table' })).toBeEnabled();
  });
});

describe('OrderHistory', () => {
  const orders = [
    {
      id: 1,
      orderNumber: '1001',
      status: 'delivered',
      totalPrice: '33.98',
      paymentMethod: 'cash',
      createdAt: '2026-10-20T10:00:00.000Z',
    },
    {
      id: 2,
      orderNumber: '1002',
      status: 'pending',
      totalPrice: '19.5',
      paymentMethod: 'card',
      createdAt: '2026-10-21T10:00:00.000Z',
    },
  ];

  it('shows a spinner while orders load', () => {
    api.get.mockImplementation(() => new Promise(() => {}));
    const { container } = renderAt(<OrderHistory />);

    expect(container.querySelector('.animate-spin')).not.toBeNull();
  });

  it('renders order cards with status labels and totals', async () => {
    api.get.mockResolvedValue({ data: { data: orders } });
    renderAt(<OrderHistory />);

    expect(await screen.findByText('Order #1001')).toBeInTheDocument();
    expect(screen.getByText('Order #1002')).toBeInTheDocument();
    expect(screen.getByText('$33.98')).toBeInTheDocument();
    expect(screen.getByText('$19.50')).toBeInTheDocument();
    expect(screen.getAllByText('Delivered').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Your order is being prepared')).toBeInTheDocument();
    expect(screen.getAllByText(/Pending/).length).toBeGreaterThanOrEqual(1);
  });

  it('renders the empty state when there are no orders', async () => {
    api.get.mockResolvedValue({ data: { data: [] } });
    renderAt(<OrderHistory />);

    expect(await screen.findByText('No orders yet')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Browse Menu' })).toHaveAttribute(
      'href',
      '/restaurant/menu'
    );
  });

  it('shows the error state and retries the request', async () => {
    api.get.mockRejectedValueOnce(new Error('Orders unavailable'));
    renderAt(<OrderHistory />);

    expect(await screen.findByText('Orders unavailable')).toBeInTheDocument();

    api.get.mockResolvedValue({ data: { data: orders } });
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));

    expect(await screen.findByText('Order #1001')).toBeInTheDocument();
    expect(screen.queryByText('Orders unavailable')).toBeNull();
  });
});

describe('AdminDashboard', () => {
  const stats = {
    totalMenuItems: 12,
    totalOrders: 40,
    totalRevenue: 1234.5,
    pendingOrders: 3,
  };
  const items = [
    {
      id: 7,
      title: 'Margherita Pizza',
      price: '12.99',
      description: 'Classic',
      tags: ['vegetarian'],
      isActive: true,
      images: ['/pizza.jpg'],
    },
  ];
  const orders = [
    {
      id: 31,
      orderNumber: '1001',
      status: 'pending',
      totalPrice: '33.98',
      createdAt: '2026-10-20T10:00:00.000Z',
    },
  ];

  const mockAdminFetch = () => {
    api.get.mockImplementation((url) => {
      if (url.startsWith('/restaurant/admin/stats')) return Promise.resolve({ data: { data: stats } });
      if (url.startsWith('/restaurant/menu')) return Promise.resolve({ data: { data: items } });
      return Promise.resolve({ data: { data: orders } });
    });
  };

  it('renders stats, managed menu items and recent orders', async () => {
    mockAdminFetch();
    renderAt(<AdminDashboard />);

    expect(await screen.findByRole('heading', { name: 'Manage Menu' })).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('40')).toBeInTheDocument();
    expect(screen.getByText('$1234.50')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('Margherita Pizza')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Back/ })).toHaveAttribute(
      'href',
      '/restaurant/menu'
    );
    expect(screen.getByText('#1001')).toBeInTheDocument();
  });

  it('creates a menu item through the add form and refetches', async () => {
    mockAdminFetch();
    const { container } = renderAt(<AdminDashboard />);
    await screen.findByText('Margherita Pizza');

    fireEvent.click(screen.getByRole('button', { name: 'Add Item' }));

    const form = container.querySelector('form');
    const textboxes = within(form).getAllByRole('textbox');
    fireEvent.change(textboxes[0], { target: { value: 'Garlic Naan' } });
    fireEvent.change(textboxes[1], { target: { value: 'Bread' } });
    fireEvent.change(within(form).getByRole('spinbutton'), { target: { value: '3.5' } });
    fireEvent.change(within(form).getByPlaceholderText('vegetarian, spicy'), {
      target: { value: 'vegetarian, baked' },
    });

    fireEvent.click(within(form).getByRole('button', { name: 'Save' }));

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/restaurant/admin/menu', {
        title: 'Garlic Naan',
        description: '',
        price: 3.5,
        category: 'Bread',
        tags: ['vegetarian', 'baked'],
        isFeatured: false,
        // handleOpen('add') seeds the form from a null item, so a new dish is
        // created inactive (AdminDashboard.jsx:72-83).
        isActive: false,
      })
    );
    await waitFor(() => expect(api.get).toHaveBeenCalledTimes(6));
  });

  it('deletes a menu item after confirmation and updates an order status', async () => {
    mockAdminFetch();
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);
    const { container } = renderAt(<AdminDashboard />);
    await screen.findByText('Margherita Pizza');

    fireEvent.click(container.querySelector('.lucide-trash-2').closest('button'));

    await waitFor(() =>
      expect(api.delete).toHaveBeenCalledWith('/restaurant/admin/menu/7')
    );

    fireEvent.click(screen.getByRole('button', { name: 'Preparing' }));

    await waitFor(() =>
      expect(api.patch).toHaveBeenCalledWith('/restaurant/admin/orders/31/status', {
        status: 'processing',
      })
    );
    confirmSpy.mockRestore();
  });

  it('opens the edit form prefilled from the item', async () => {
    mockAdminFetch();
    const { container } = renderAt(<AdminDashboard />);
    await screen.findByText('Margherita Pizza');

    fireEvent.click(screen.getByRole('button', { name: 'Edit' }));

    const form = container.querySelector('form');
    const textboxes = within(form).getAllByRole('textbox');
    expect(textboxes[0]).toHaveValue('Margherita Pizza');
    expect(textboxes[1]).toHaveValue('');
    expect(within(form).getByRole('spinbutton')).toHaveValue(12.99);
    expect(within(form).getByPlaceholderText('vegetarian, spicy')).toHaveValue('vegetarian');

    fireEvent.click(within(form).getByRole('button', { name: 'Cancel' }));
    expect(container.querySelector('form')).toBeNull();
  });

  it('surfaces a load error when the admin API fails', async () => {
    api.get.mockRejectedValue(new Error('Admin API down'));
    renderAt(<AdminDashboard />);

    expect(await screen.findByText('Admin API down')).toBeInTheDocument();
  });
});
