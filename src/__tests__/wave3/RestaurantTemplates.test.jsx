import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import RestaurantMenu from '../../templates/restaurant/RestaurantMenu/RestaurantMenu';
import ReservationSystem from '../../templates/restaurant/ReservationSystem/ReservationSystem';
import OnlineOrders from '../../templates/restaurant/OnlineOrders/OnlineOrders';
import ChefMenu from '../../templates/restaurant/ChefMenu/ChefMenu';
import RestaurantEvents from '../../templates/restaurant/RestaurantEvents/RestaurantEvents';

/** Restaurant template pages render local mock data and need only a router. */
function renderTemplate(ui) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe('RestaurantMenu template', () => {
  it('renders the hero, stats, and the full menu with add actions', () => {
    renderTemplate(<RestaurantMenu />);

    expect(
      screen.getByRole('heading', { level: 1, name: 'Restaurant & Menu' })
    ).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Spice Garden Restaurant' })).toBeInTheDocument();
    expect(screen.getByText('Open Now')).toBeInTheDocument();
    expect(screen.getByText('Menu Items')).toBeInTheDocument();
    expect(screen.getByText('Customer Reviews')).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: '+ Add' })).toHaveLength(8);
    expect(screen.getByText('PKR 950')).toBeInTheDocument();
  });

  it('filters the menu down to a category', () => {
    renderTemplate(<RestaurantMenu />);

    fireEvent.click(screen.getByRole('button', { name: 'Starters' }));

    expect(screen.getAllByRole('button', { name: '+ Add' })).toHaveLength(2);
    expect(screen.getByText('Crispy Chicken Rolls')).toBeInTheDocument();
    expect(screen.getByText('Paneer Tikka')).toBeInTheDocument();
    expect(screen.queryByText('Biryani Special')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Mains' }));
    expect(screen.getAllByRole('button', { name: '+ Add' })).toHaveLength(3);
    expect(screen.getByText('Biryani Special')).toBeInTheDocument();
  });

  it('adds items to the cart, changes quantity, and clears the order', () => {
    renderTemplate(<RestaurantMenu />);

    fireEvent.click(screen.getAllByRole('button', { name: '+ Add' })[0]);

    expect(screen.getByRole('heading', { name: 'Your Order (1 items)' })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Increase quantity' }));
    expect(screen.getByRole('heading', { name: 'Your Order (2 items)' })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Clear Cart' }));
    expect(screen.queryByRole('heading', { name: /Your Order/ })).toBeNull();
  });

  it('toggles a dish favorite from the menu card', () => {
    renderTemplate(<RestaurantMenu />);

    fireEvent.click(screen.getAllByRole('button', { name: 'Add to favorites' })[0]);

    expect(screen.getByRole('button', { name: /Favorites \(1\)/ })).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Remove from favorites' })).toHaveLength(2);
  });
});

describe('ReservationSystem template', () => {
  it('renders the booking form with slots, party sizes, and occasions', () => {
    renderTemplate(<ReservationSystem />);

    expect(
      screen.getByRole('heading', { level: 1, name: 'Table Reservation' })
    ).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Your Table Awaits' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Book a table' })).toBeInTheDocument();
    expect(screen.getByPlaceholderText('e.g. Ayesha Khan')).toBeInTheDocument();
    expect(screen.getByDisplayValue('2026-09-15')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Birthday' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /12:30 PM/ })).toBeEnabled();
    expect(screen.getByRole('button', { name: /1:30 PM/ })).toBeDisabled();
  });

  it('keeps the confirm action disabled until an available slot is picked', () => {
    renderTemplate(<ReservationSystem />);

    const confirm = screen.getByRole('button', { name: /Confirm Reservation/ });
    expect(confirm).toBeDisabled();

    fireEvent.click(screen.getByRole('button', { name: /1:30 PM/ }));
    expect(confirm).toBeDisabled();

    fireEvent.click(screen.getByRole('button', { name: /7:00 PM/ }));
    expect(confirm).toBeEnabled();
  });

  it('confirms the reservation with party size and occasion details', () => {
    renderTemplate(<ReservationSystem />);

    fireEvent.click(screen.getByRole('button', { name: '4' }));
    fireEvent.click(screen.getByRole('button', { name: 'Birthday' }));
    fireEvent.click(screen.getByRole('button', { name: /12:30 PM/ }));
    fireEvent.click(screen.getByRole('button', { name: /Confirm Reservation/ }));

    expect(screen.getByRole('heading', { name: 'Reservation Confirmed!' })).toBeInTheDocument();
    const summary = screen.getByText(/Table for/);
    expect(summary.textContent).toContain('4');
    expect(summary.textContent).toContain('12:30 PM');
    expect(summary.textContent).toContain('Birthday');

    fireEvent.click(screen.getByRole('button', { name: 'Make Another Booking' }));
    expect(screen.getByRole('heading', { name: 'Book a table' })).toBeInTheDocument();
  });
});

describe('OnlineOrders template', () => {
  it('renders the active order with its delivery stepper and promise', () => {
    renderTemplate(<OnlineOrders />);

    expect(
      screen.getByRole('heading', { level: 1, name: 'Online Orders & Delivery' })
    ).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Order #ORD-8391' })).toBeInTheDocument();
    expect(screen.getByText('Chicken Biryani, Garlic Naan ×2, Raita')).toBeInTheDocument();
    expect(screen.getByText('Rs 1,640')).toBeInTheDocument();
    expect(screen.getByText('10 min')).toBeInTheDocument();

    for (const step of [
      'Order Received',
      'Being Prepared',
      'Ready for Pickup',
      'Delivered',
    ]) {
      expect(screen.getByText(step)).toBeInTheDocument();
    }
    expect(screen.getByText('Our Delivery Promise')).toBeInTheDocument();
    expect(screen.getByText('72% of orders arrive within 40 minutes')).toBeInTheDocument();
  });

  it('switches the tracked order when another order chip is clicked', () => {
    renderTemplate(<OnlineOrders />);

    fireEvent.click(screen.getByRole('button', { name: '#ORD-8390' }));

    expect(screen.getByRole('heading', { name: 'Order #ORD-8390' })).toBeInTheDocument();
    expect(screen.getByText('Rs 980')).toBeInTheDocument();
    expect(screen.getByText('25 min')).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Order #ORD-8391' })).toBeNull();
  });

  it('exposes the on-time delivery progress as an accessible bar', () => {
    renderTemplate(<OnlineOrders />);

    const progress = screen.getByRole('progressbar', { name: 'Progress' });
    expect(progress).toHaveAttribute('aria-valuenow', '72');
    expect(progress).toHaveAttribute('aria-valuemax', '100');
  });
});

describe('ChefMenu template', () => {
  it('renders the chef hero, signature dishes, and note', () => {
    renderTemplate(<ChefMenu />);

    expect(
      screen.getByRole('heading', { level: 1, name: "Chef's Signature Menu" })
    ).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Chef Imran Qureshi' })).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Add to Order' })).toHaveLength(6);
    expect(screen.getByText('Nihari with Bheja')).toBeInTheDocument();
    expect(screen.getByText('Rs 1,150')).toBeInTheDocument();
    expect(screen.getByText("Chef's Note")).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'View Full Menu' })).toBeInTheDocument();
  });

  it('filters the signature dishes by course', () => {
    renderTemplate(<ChefMenu />);

    fireEvent.click(screen.getByRole('button', { name: 'Desserts' }));

    expect(screen.getAllByRole('button', { name: 'Add to Order' })).toHaveLength(2);
    expect(screen.getByText('Kheer Angoori')).toBeInTheDocument();
    expect(screen.getByText('Kunafa Cheesecake')).toBeInTheDocument();
    expect(screen.queryByText('Nihari with Bheja')).toBeNull();
  });

  it('restores every course after choosing All', () => {
    renderTemplate(<ChefMenu />);

    fireEvent.click(screen.getByRole('button', { name: 'Starters' }));
    expect(screen.getAllByRole('button', { name: 'Add to Order' })).toHaveLength(2);

    fireEvent.click(screen.getByRole('button', { name: 'All' }));
    expect(screen.getAllByRole('button', { name: 'Add to Order' })).toHaveLength(6);
  });
});

describe('RestaurantEvents template', () => {
  it('renders the hero, packages, gallery, and included features', () => {
    renderTemplate(<RestaurantEvents />);

    expect(
      screen.getByRole('heading', { level: 1, name: 'Private Dining & Events' })
    ).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Celebrate With Us' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Choose Your Package' })).toBeInTheDocument();
    expect(screen.getByText('Wedding & Nikkah')).toBeInTheDocument();
    expect(screen.getByText('Rs 150,000')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Venue Gallery' })).toBeInTheDocument();
    expect(screen.getByText('Live entertainment included')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Reserve Date/ })).toBeInTheDocument();
  });

  it('selects a package on click and moves the highlight', () => {
    renderTemplate(<RestaurantEvents />);

    const wedding = screen.getByText('Wedding & Nikkah').closest('[role="button"]');
    const casual = screen.getByText('Casual Gathering').closest('[role="button"]');
    expect(wedding).toHaveClass('border-primary');

    fireEvent.click(casual);

    expect(casual).toHaveClass('border-primary');
    expect(wedding).not.toHaveClass('border-primary');
  });

  it('supports keyboard selection of a package', () => {
    renderTemplate(<RestaurantEvents />);

    const corporate = screen.getByText('Corporate & Launch').closest('[role="button"]');
    expect(corporate).not.toHaveClass('border-primary');

    fireEvent.keyDown(corporate, { key: 'Enter' });

    expect(corporate).toHaveClass('border-primary');
  });
});
