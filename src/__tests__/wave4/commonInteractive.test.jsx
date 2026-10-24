import { afterAll, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';

const { toastState, licenseState, contactState, designState, notificationsAPI, toastDismiss } =
  vi.hoisted(() => ({
    toastState: { current: { notifications: [], addNotification: vi.fn(), dismissNotification: vi.fn() } },
    licenseState: { current: { valid: false, trial: true, status: 'trial' } },
    contactState: { postLead: vi.fn() },
    designState: {
      current: {
        designStyle: 'balanced',
        setDesignStyle: vi.fn(),
        layoutType: 'standard',
        setLayoutType: vi.fn(),
        autoMode: false,
        toggleAutoMode: vi.fn(),
        isDark: true,
        toggleDarkMode: vi.fn(),
        availableStyles: [],
        availableLayouts: [],
      },
    },
    notificationsAPI: { getAll: vi.fn(), markAllRead: vi.fn() },
    toastDismiss: vi.fn(),
  }));

vi.mock('../../context/NotificationContext', () => ({
  useNotifications: () => toastState.current,
}));

vi.mock('../../hooks/useLicense', () => ({
  default: () => licenseState.current,
}));

vi.mock('../../services/contact', () => ({
  contactAPI: contactState,
}));

vi.mock('../../context/DesignSystemContext', () => ({
  useDesignSystem: () => designState.current,
}));

vi.mock('../../services/api', () => ({ notificationsAPI }));

vi.mock('../../components/common/ThemeProvider', () => ({
  useTheme: () => ({ theme: 'dark', isDark: true }),
}));

import ThemeSwitcher from '../../components/common/ThemeSwitcher';
import ToastRegion from '../../components/common/ToastRegion';
import NewsletterSignup from '../../components/common/NewsletterSignup';
import FooterNewsletter from '../../components/common/FooterNewsletter';
import ContactForm from '../../components/common/ContactForm';
import CookieConsent from '../../components/common/CookieConsent';
import PWAInstallBanner from '../../components/common/PWAInstallBanner';
import RouteErrorBoundary from '../../components/common/RouteErrorBoundary';
import CaptchaTurnstile from '../../components/common/CaptchaTurnstile';
import LicenseWatermark from '../../components/common/LicenseWatermark';
import NotificationBell from '../../components/common/NotificationBell';
import ThemeCustomizer from '../../components/common/ThemeCustomizer';

const renderWithQuery = (ui) => {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 }, mutations: { retry: false } },
  });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
};

let originalMatchMedia;

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  document.documentElement.classList.remove('dark', 'light');
  document.documentElement.style.colorScheme = '';
  document.documentElement.style.removeProperty('--color-primary');
  document.documentElement.style.removeProperty('--color-accent');

  originalMatchMedia = window.matchMedia;
  window.matchMedia = vi.fn(() => ({
    matches: false,
    media: '',
    onchange: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));

  toastState.current = {
    notifications: [],
    addNotification: vi.fn(),
    dismissNotification: toastDismiss,
  };
  licenseState.current = { valid: false, trial: true, status: 'trial' };
  contactState.postLead.mockResolvedValue({ ok: true, provider: 'mock', mock: true });
  notificationsAPI.getAll.mockResolvedValue({ data: { data: [] } });
  notificationsAPI.markAllRead.mockResolvedValue({ data: {} });
});

afterAll(() => {
  window.matchMedia = originalMatchMedia;
});

describe('ThemeSwitcher', () => {
  it('defaults to system and persists the resolved scheme', () => {
    render(<ThemeSwitcher />);

    expect(screen.getByRole('button', { name: 'system theme' })).toHaveAttribute(
      'aria-pressed',
      'true'
    );
    expect(document.documentElement.classList.contains('dark')).toBe(false);
    expect(document.documentElement.style.colorScheme).toBe('light');
    expect(localStorage.getItem('theme')).toBe('system');
  });

  it('applies and stores the dark theme', () => {
    render(<ThemeSwitcher defaultTheme="light" />);

    fireEvent.click(screen.getByRole('button', { name: 'dark theme' }));

    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(document.documentElement.style.colorScheme).toBe('dark');
    expect(localStorage.getItem('theme')).toBe('dark');
    expect(screen.getByRole('button', { name: 'dark theme' })).toHaveAttribute(
      'aria-pressed',
      'true'
    );
  });

  it('returns to the light theme and honours a custom storage key', () => {
    render(<ThemeSwitcher defaultTheme="dark" storageKey="ui-theme" />);

    expect(document.documentElement.classList.contains('dark')).toBe(true);
    fireEvent.click(screen.getByRole('button', { name: 'light theme' }));

    expect(document.documentElement.classList.contains('dark')).toBe(false);
    expect(localStorage.getItem('ui-theme')).toBe('light');
  });
});

describe('ToastRegion', () => {
  it('renders notifications with their tone and dismisses them', () => {
    toastState.current.notifications = [
      { id: 'a', message: 'Saved successfully', type: 'success' },
      { id: 'b', message: 'Upload failed', type: 'error' },
      { id: 'c', message: 'Heads up', type: 'info' },
    ];

    render(<ToastRegion />);

    expect(screen.getByRole('region', { name: 'Notifications' })).toBeInTheDocument();
    expect(screen.getByText('Saved successfully')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent('Upload failed');
    expect(screen.getAllByRole('status').length).toBeGreaterThanOrEqual(1);

    fireEvent.click(screen.getAllByRole('button', { name: 'Dismiss notification' })[0]);
    expect(toastDismiss).toHaveBeenCalledWith('a');
  });

  it('renders nothing when there are no notifications', () => {
    const { container } = render(<ToastRegion />);
    expect(container).toBeEmptyDOMElement();
  });
});

describe('NewsletterSignup', () => {
  it('submits the email and swaps the form for a success message', async () => {
    const onSubscribe = vi.fn().mockResolvedValue(undefined);
    render(<NewsletterSignup onSubscribe={onSubscribe} />);

    expect(screen.getByRole('heading', { name: 'Stay in the loop' })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Email address'), {
      target: { value: 'ada@example.com' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Subscribe/ }));

    expect(
      await screen.findByText('Thanks! Please check your inbox to confirm.')
    ).toBeInTheDocument();
    expect(onSubscribe).toHaveBeenCalledWith('ada@example.com');
    expect(screen.queryByLabelText('Email address')).toBeNull();
  });

  it('keeps the form when the subscription request fails', async () => {
    const onSubscribe = vi.fn().mockRejectedValue(new Error('offline'));
    render(<NewsletterSignup onSubscribe={onSubscribe} />);

    fireEvent.change(screen.getByLabelText('Email address'), {
      target: { value: 'ada@example.com' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Subscribe/ }));

    await waitFor(() => expect(onSubscribe).toHaveBeenCalled());
    expect(screen.getByLabelText('Email address')).toBeInTheDocument();
    expect(screen.queryByText(/Thanks! Please check/)).toBeNull();
  });
});

describe('FooterNewsletter', () => {
  it('rejects an invalid address without calling the API', async () => {
    render(<FooterNewsletter />);

    fireEvent.change(screen.getByLabelText('Email address'), {
      target: { value: 'not-an-email' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Subscribe' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Enter a valid email address.');
    expect(contactState.postLead).not.toHaveBeenCalled();
  });

  it('reports the unconfigured provider instead of faking success', async () => {
    render(<FooterNewsletter />);

    fireEvent.change(screen.getByLabelText('Email address'), {
      target: { value: 'ada@example.com' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Subscribe' }));

    expect(await screen.findByText(/not configured here/)).toBeInTheDocument();
    expect(contactState.postLead).toHaveBeenCalledWith(
      expect.objectContaining({ email: 'ada@example.com', consent: true })
    );
    expect(screen.getByLabelText('Email address')).toHaveValue('ada@example.com');
  });

  it('confirms a real delivery and clears the field', async () => {
    contactState.postLead.mockResolvedValue({ ok: true, provider: 'formspree' });
    render(<FooterNewsletter />);

    fireEvent.change(screen.getByLabelText('Email address'), {
      target: { value: 'ada@example.com' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Subscribe' }));

    expect(await screen.findByText(/check your inbox to confirm/)).toBeInTheDocument();
    expect(screen.getByLabelText('Email address')).toHaveValue('');
  });
});

describe('ContactForm', () => {
  it('validates required fields and consent before submitting', () => {
    render(<ContactForm />);

    fireEvent.click(screen.getByRole('button', { name: 'Send message' }));

    expect(screen.getByText('Name is required')).toBeInTheDocument();
    expect(screen.getByText('Email is required')).toBeInTheDocument();
    expect(screen.getByText('Message is required')).toBeInTheDocument();
    expect(screen.getByText('Please accept the privacy policy')).toBeInTheDocument();
    expect(contactState.postLead).not.toHaveBeenCalled();
  });

  it('submits a valid inquiry and reports success', async () => {
    const onSuccess = vi.fn();
    render(<ContactForm onSuccess={onSuccess} />);

    fireEvent.change(screen.getByRole('textbox', { name: /^Name/ }), {
      target: { value: 'Ada Lovelace' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /^Email/ }), {
      target: { value: 'ada@example.com' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /^Message/ }), {
      target: { value: 'I would like a demo of the platform.' },
    });
    fireEvent.click(screen.getByRole('checkbox'));

    fireEvent.click(screen.getByRole('button', { name: 'Send message' }));

    expect(await screen.findByText(/Message queued/)).toBeInTheDocument();
    expect(contactState.postLead).toHaveBeenCalledWith({
      name: 'Ada Lovelace',
      email: 'ada@example.com',
      subject: 'Website contact',
      message: 'I would like a demo of the platform.',
      consent: true,
    });
    expect(onSuccess).toHaveBeenCalledWith({ ok: true, provider: 'mock', mock: true });
  });

  it('surfaces a delivery failure through onError', async () => {
    contactState.postLead.mockRejectedValue(new Error('network'));
    const onError = vi.fn();
    render(<ContactForm onError={onError} />);

    fireEvent.change(screen.getByRole('textbox', { name: /^Name/ }), {
      target: { value: 'Ada' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /^Email/ }), {
      target: { value: 'ada@example.com' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /^Message/ }), {
      target: { value: 'A long enough message.' },
    });
    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.click(screen.getByRole('button', { name: 'Send message' }));

    expect(await screen.findByText(/could not send your message/)).toBeInTheDocument();
    expect(onError).toHaveBeenCalled();
  });
});

describe('CookieConsent', () => {
  it('shows on a first visit and stores the accepted decision', async () => {
    const onConsent = vi.fn();
    window.addEventListener('cookieConsentUpdated', onConsent);
    render(<CookieConsent />);

    expect(await screen.findByRole('dialog')).toHaveAccessibleName('We value your privacy');
    fireEvent.click(screen.getByRole('button', { name: 'Accept All' }));

    expect(screen.queryByRole('dialog')).toBeNull();
    expect(JSON.parse(localStorage.getItem('lumicorepro_cookie_consent'))).toEqual({
      essential: true,
      analytics: true,
      marketing: true,
    });
    expect(onConsent).toHaveBeenCalledTimes(1);
    window.removeEventListener('cookieConsentUpdated', onConsent);
  });

  it('stays hidden when a decision already exists', () => {
    localStorage.setItem(
      'lumicorepro_cookie_consent',
      JSON.stringify({ essential: true, analytics: false, marketing: false })
    );
    const { container } = render(<CookieConsent />);
    expect(container).toBeEmptyDOMElement();
  });

  it('re-opens for cookie preferences and can be dismissed', async () => {
    localStorage.setItem(
      'lumicorepro_cookie_consent',
      JSON.stringify({ essential: true, analytics: false, marketing: false })
    );
    render(<CookieConsent />);

    act(() => {
      window.dispatchEvent(new Event('cookiePreferences'));
    });

    const dialog = await screen.findByRole('dialog');
    expect(dialog).toBeInTheDocument();
    expect(localStorage.getItem('lumicorepro_cookie_consent')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Close' }));
    expect(screen.queryByRole('dialog')).toBeNull();
  });
});

describe('PWAInstallBanner', () => {
  const makeInstallPrompt = (outcome = 'accepted') => {
    const event = new Event('beforeinstallprompt');
    event.prompt = vi.fn();
    event.userChoice = Promise.resolve({ outcome });
    return event;
  };

  const dispatch = (event) =>
    act(() => {
      window.dispatchEvent(event);
    });

  it('appears on beforeinstallprompt and installs the app', async () => {
    render(<PWAInstallBanner appName="Lumi App" />);
    const event = makeInstallPrompt('accepted');
    dispatch(event);

    expect(await screen.findByRole('region', { name: 'App install banner' })).toBeInTheDocument();
    expect(screen.getByText('Lumi App')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Install' }));

    await waitFor(() => expect(event.prompt).toHaveBeenCalledTimes(1));
    await waitFor(() =>
      expect(localStorage.getItem('pwa_install_dismissed')).toBe('1')
    );
    expect(screen.queryByRole('region', { name: 'App install banner' })).toBeNull();
  });

  it('stays dismissed when a previous dismissal is stored', async () => {
    localStorage.setItem('pwa_install_dismissed', '1');
    const { container } = render(<PWAInstallBanner />);
    dispatch(makeInstallPrompt());

    await waitFor(() => expect(container).toBeEmptyDOMElement());
  });

  it('dismisses and remembers the choice', async () => {
    render(<PWAInstallBanner />);
    dispatch(makeInstallPrompt());
    await screen.findByRole('region', { name: 'App install banner' });

    fireEvent.click(screen.getByRole('button', { name: 'Dismiss install banner' }));

    expect(screen.queryByRole('region', { name: 'App install banner' })).toBeNull();
    expect(localStorage.getItem('pwa_install_dismissed')).toBe('1');
  });
});

describe('RouteErrorBoundary', () => {
  it('renders a 404 response error and navigates home', async () => {
    const router = createMemoryRouter(
      [
        { path: '/', element: <div>home-page</div> },
        {
          path: '/broken',
          loader: () => {
            throw new Response(null, { status: 404, statusText: 'Missing' });
          },
          errorElement: <RouteErrorBoundary />,
        },
      ],
      { initialEntries: ['/broken'] }
    );

    render(<RouterProvider router={router} />);

    expect(
      await screen.findByRole('heading', { name: 'Page unavailable (404)' })
    ).toBeInTheDocument();
    expect(screen.getByText(/could not load this page/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Go home/ }));
    expect(await screen.findByText('home-page')).toBeInTheDocument();
  });

  it('renders an unexpected error with its detail in development', async () => {
    const router = createMemoryRouter(
      [
        {
          path: '/',
          loader: () => {
            throw new Error('loader exploded');
          },
          errorElement: <RouteErrorBoundary />,
        },
      ],
      { initialEntries: ['/'] }
    );

    render(<RouterProvider router={router} />);

    expect(
      await screen.findByRole('heading', { name: 'Something went wrong' })
    ).toBeInTheDocument();
    expect(screen.getByText('loader exploded')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Try again/ })).toBeInTheDocument();
  });
});

describe('CaptchaTurnstile', () => {
  it('reports a missing site key', () => {
    render(<CaptchaTurnstile onVerify={vi.fn()} />);

    expect(screen.getByRole('alert')).toHaveTextContent('Captcha site key not configured.');
  });

  it('renders the Turnstile widget, forwards the token and cleans up', async () => {
    const onVerify = vi.fn();
    const widgetRender = vi.fn((element, options) => {
      options.callback('token-123');
      return 'widget-1';
    });
    window.turnstile = { render: widgetRender, remove: vi.fn() };

    const { unmount } = render(<CaptchaTurnstile siteKey="site-key" onVerify={onVerify} />);

    await waitFor(() => expect(widgetRender).toHaveBeenCalledTimes(1));
    expect(widgetRender.mock.calls[0][1]).toMatchObject({
      sitekey: 'site-key',
      theme: 'dark',
      size: 'normal',
    });
    expect(onVerify).toHaveBeenCalledWith('token-123');

    unmount();
    expect(window.turnstile.remove).toHaveBeenCalledWith('widget-1');
    delete window.turnstile;
  });
});

describe('LicenseWatermark', () => {
  it('renders the trial watermark and activation action', () => {
    const onActivate = vi.fn();
    const { container } = render(<LicenseWatermark onActivate={onActivate} />);

    expect(container.textContent).toContain('LumicorePro · Trial Mode');
    fireEvent.click(container.querySelector('button'));
    expect(onActivate).toHaveBeenCalledTimes(1);
  });

  it('hides itself for an active license', () => {
    licenseState.current = { valid: true, trial: false, status: 'active' };
    const { container } = render(<LicenseWatermark />);
    expect(container).toBeEmptyDOMElement();
  });

  it('hides itself when no key is present', () => {
    licenseState.current = { valid: false, trial: true, status: 'no_key' };
    const { container } = render(<LicenseWatermark />);
    expect(container).toBeEmptyDOMElement();
  });
});

describe('NotificationBell', () => {
  const items = [
    {
      id: 1,
      title: 'Order shipped',
      message: 'Your order is on the way',
      type: 'success',
      read: false,
      createdAt: new Date().toISOString(),
    },
    {
      id: 2,
      title: 'Payment failed',
      message: 'Please retry your card',
      type: 'warning',
      read: false,
      createdAt: new Date(Date.now() - 120000).toISOString(),
    },
    {
      id: 3,
      title: 'Welcome',
      message: 'Thanks for joining',
      type: 'info',
      read: true,
      createdAt: new Date(Date.now() - 7200000).toISOString(),
    },
  ];

  it('shows the unread badge and the notification list', async () => {
    notificationsAPI.getAll.mockResolvedValue({ data: { data: items } });
    renderWithQuery(<NotificationBell />);

    expect(await screen.findByText('2')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Notifications' }));

    expect(screen.getByText('Order shipped')).toBeInTheDocument();
    expect(screen.getByText('Payment failed')).toBeInTheDocument();
    expect(screen.getByText('Thanks for joining')).toBeInTheDocument();
    expect(screen.getByText('2m ago')).toBeInTheDocument();
    expect(notificationsAPI.getAll).toHaveBeenCalledWith({ limit: 10 });
  });

  it('marks every notification as read', async () => {
    notificationsAPI.getAll.mockResolvedValue({ data: { data: items } });
    renderWithQuery(<NotificationBell />);
    await screen.findByText('2');

    fireEvent.click(screen.getByRole('button', { name: 'Notifications' }));
    fireEvent.click(screen.getByRole('button', { name: 'Mark all read' }));

    await waitFor(() => expect(notificationsAPI.markAllRead).toHaveBeenCalledTimes(1));
  });

  it('shows the empty state when the inbox is clear', async () => {
    renderWithQuery(<NotificationBell />);
    fireEvent.click(await screen.findByRole('button', { name: 'Notifications' }));

    expect(await screen.findByText('No notifications')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Mark all read' })).toBeNull();
  });
});

describe('ThemeCustomizer', () => {
  it('opens the drawer and applies a colour palette', () => {
    render(<ThemeCustomizer />);

    const trigger = screen.getByRole('button', { name: 'Open theme customizer' });
    expect(trigger).toHaveAttribute('aria-expanded', 'false');

    fireEvent.click(trigger);
    expect(trigger).toHaveAttribute('aria-expanded', 'true');

    fireEvent.click(screen.getByRole('button', { name: /Royal Violet/ }));

    expect(document.documentElement.style.getPropertyValue('--color-primary')).toBe(
      'rgb(139, 92, 246)'
    );
    expect(document.documentElement.style.getPropertyValue('--color-accent')).toBe(
      'rgb(168, 85, 247)'
    );
    expect(localStorage.getItem('site_theme')).toBe('violet');
  });

  it('closes on Escape and restores focus to the trigger', () => {
    render(<ThemeCustomizer />);
    const trigger = screen.getByRole('button', { name: 'Open theme customizer' });
    fireEvent.click(trigger);

    fireEvent.keyDown(window, { key: 'Escape' });

    expect(trigger).toHaveAttribute('aria-expanded', 'false');
    expect(document.activeElement).toBe(trigger);
  });

  it('restores a saved palette on mount', () => {
    localStorage.setItem('site_theme', 'emerald');
    render(<ThemeCustomizer />);

    expect(document.documentElement.style.getPropertyValue('--color-primary')).toBe(
      'rgb(16, 185, 129)'
    );
  });
});
