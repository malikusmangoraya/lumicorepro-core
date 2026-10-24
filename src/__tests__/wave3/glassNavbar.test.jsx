import { fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const appState = vi.hoisted(() => ({
  isAuthenticated: false,
  logout: vi.fn(),
  language: 'en',
  setLanguage: vi.fn(),
}));

const themeState = vi.hoisted(() => ({ theme: 'dark', toggleTheme: vi.fn() }));

vi.mock('../../context/AppContext', () => ({
  useAppContext: () => appState,
}));

vi.mock('../../components/common/ThemeProvider', () => ({
  useTheme: () => themeState,
}));

vi.mock('../../components/common/BrandLogo', () => ({
  default: () => <div data-testid="brand-logo" />,
}));

vi.mock('../../components/common/Language', () => ({
  default: () => <div data-testid="language-switcher" />,
}));

vi.mock('../../components/common/NotificationBell', () => ({
  default: () => <div data-testid="notification-bell" />,
}));

vi.mock('../../components/common/CurrencySelector', () => ({
  CurrencySelector: () => <div data-testid="currency-selector" />,
}));

import GlassNavbar from '../../components/common/GlassNavbar';

function LocationProbe() {
  const location = useLocation();
  return <div data-testid="location">{`${location.pathname}${location.search}`}</div>;
}

function renderNav(route = '/') {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <GlassNavbar />
      <LocationProbe />
    </MemoryRouter>
  );
}

beforeEach(() => {
  appState.isAuthenticated = false;
  appState.logout.mockReset();
  appState.setLanguage.mockReset();
  themeState.theme = 'dark';
  themeState.toggleTheme.mockReset();
});

describe('GlassNavbar', () => {
  it('renders the desktop links and marks the exact active route', () => {
    renderNav('/pricing');

    const nav = screen.getByRole('navigation', { name: 'Main navigation' });
    const pricing = within(nav).getByRole('link', { name: 'Pricing' });
    expect(pricing).toHaveAttribute('href', '/pricing');
    expect(pricing).toHaveAttribute('aria-current', 'page');

    const home = within(nav).getByRole('link', { name: 'Home' });
    expect(home).toHaveAttribute('href', '/');
    expect(home).not.toHaveAttribute('aria-current');

    expect(within(nav).getByRole('link', { name: 'Templates' })).toHaveAttribute(
      'href',
      '/templates'
    );
  });

  it('treats the templates prefix group as active on nested template routes', () => {
    renderNav('/templates/ecommerce/ProductListing');

    const nav = screen.getByRole('navigation', { name: 'Main navigation' });
    expect(within(nav).getByRole('link', { name: 'Templates' })).toHaveAttribute(
      'aria-current',
      'page'
    );
    expect(within(nav).getByRole('link', { name: 'Shop' })).toHaveAttribute(
      'aria-current',
      'page'
    );
    expect(within(nav).getByRole('link', { name: 'Pricing' })).not.toHaveAttribute('aria-current');
  });

  it('routes anonymous visitors to login/register and toggles the theme', () => {
    renderNav('/');

    expect(screen.queryByTestId('notification-bell')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Login' }));
    expect(screen.getByTestId('location')).toHaveTextContent('/login');

    fireEvent.click(screen.getByRole('button', { name: 'Register' }));
    expect(screen.getByTestId('location')).toHaveTextContent('/register');

    const themeButton = screen.getByRole('button', { name: 'Switch to light mode' });
    fireEvent.click(themeButton);
    expect(themeState.toggleTheme).toHaveBeenCalledTimes(1);
  });

  it('switches the theme toggle label in light mode', () => {
    themeState.theme = 'light';
    renderNav('/');

    expect(screen.getByRole('button', { name: 'Switch to dark mode' })).toBeInTheDocument();
  });

  it('opens the mobile drawer and closes it from the close control or backdrop', () => {
    renderNav('/');

    fireEvent.click(screen.getByRole('button', { name: 'Open menu' }));

    let dialog = screen.getByRole('dialog', { name: 'Mobile navigation' });
    expect(within(dialog).getByText('More Templates')).toBeInTheDocument();
    expect(within(dialog).getByRole('link', { name: 'Restaurant' })).toHaveAttribute(
      'href',
      '/templates/restaurant/RestaurantMenu'
    );

    fireEvent.click(dialog.parentElement.firstElementChild);
    expect(screen.queryByRole('dialog', { name: 'Mobile navigation' })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Open menu' }));
    dialog = screen.getByRole('dialog', { name: 'Mobile navigation' });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Close menu' }));
    expect(screen.queryByRole('dialog', { name: 'Mobile navigation' })).not.toBeInTheDocument();
  });

  it('handles login/register and logout from the mobile drawer footer', () => {
    const { unmount } = renderNav('/');

    fireEvent.click(screen.getByRole('button', { name: 'Open menu' }));
    let dialog = screen.getByRole('dialog', { name: 'Mobile navigation' });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Create Account' }));
    expect(screen.getByTestId('location')).toHaveTextContent('/register');
    expect(screen.queryByRole('dialog', { name: 'Mobile navigation' })).not.toBeInTheDocument();

    unmount();
    appState.isAuthenticated = true;
    renderNav('/');

    fireEvent.click(screen.getByRole('button', { name: 'Open menu' }));
    dialog = screen.getByRole('dialog', { name: 'Mobile navigation' });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Logout' }));

    expect(appState.logout).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('dialog', { name: 'Mobile navigation' })).not.toBeInTheDocument();
  });

  it('closes the mobile drawer when a link navigates', () => {
    renderNav('/');

    fireEvent.click(screen.getByRole('button', { name: 'Open menu' }));
    const dialog = screen.getByRole('dialog', { name: 'Mobile navigation' });

    fireEvent.click(within(dialog).getByRole('link', { name: 'Templates' }));

    expect(screen.getByTestId('location')).toHaveTextContent('/templates');
    expect(screen.queryByRole('dialog', { name: 'Mobile navigation' })).not.toBeInTheDocument();
  });

  it('shows the account menu for authenticated users and logs out', () => {
    appState.isAuthenticated = true;
    renderNav('/');

    expect(screen.getByTestId('notification-bell')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Account menu' }));
    const menu = screen.getByRole('menu');
    expect(within(menu).getByRole('menuitem', { name: 'Profile' })).toBeInTheDocument();

    fireEvent.click(within(menu).getByRole('menuitem', { name: 'Logout' }));
    expect(appState.logout).toHaveBeenCalledTimes(1);
  });
});
