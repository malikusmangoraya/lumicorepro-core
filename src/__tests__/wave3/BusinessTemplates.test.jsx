import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import LandingPage from '../../templates/business/LandingPage/LandingPage';
import ServicesPage from '../../templates/business/ServicesPage/ServicesPage';
import PortfolioPage from '../../templates/business/PortfolioPage/PortfolioPage';
import PricingPage from '../../templates/business/PricingPage/PricingPage';
import ContactPage from '../../templates/business/ContactPage/ContactPage';

/**
 * Business template pages are presentational: local mock data plus a router
 * for the TemplateShell "Templates" back link.
 */
function renderTemplate(ui) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

afterEach(() => {
  vi.useRealTimers();
});

describe('LandingPage template', () => {
  it('renders the shell header, hero, and primary calls to action', () => {
    renderTemplate(<LandingPage />);

    expect(screen.getByRole('heading', { level: 1, name: 'Landing Page' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Ship Products People Love/ })).toBeInTheDocument();
    expect(screen.getByText(/Trusted by 10,000\+ teams worldwide/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Start for Free/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'View Live Demo' })).toBeInTheDocument();
  });

  it('renders every section heading and the trust stats', () => {
    renderTemplate(<LandingPage />);

    for (const heading of [
      'Everything you need to ship',
      'Built for modern development',
      'Loved by developers everywhere',
      'Start free, scale as you grow',
      'Start Building Today',
    ]) {
      expect(screen.getByRole('heading', { name: heading })).toBeInTheDocument();
    }

    for (const value of ['10K+', '99.9%', '50+', '24/7']) {
      expect(screen.getByText(value)).toBeInTheDocument();
    }
    expect(screen.getByText('Teams Worldwide')).toBeInTheDocument();
  });

  it('shows all pricing tiers with their monthly prices and CTAs', () => {
    renderTemplate(<LandingPage />);

    for (const name of ['Starter', 'Pro', 'Enterprise']) {
      expect(screen.getByRole('heading', { name })).toBeInTheDocument();
    }
    expect(screen.getByText('$0')).toBeInTheDocument();
    expect(screen.getByText('$29')).toBeInTheDocument();
    expect(screen.getByText('$99')).toBeInTheDocument();
    expect(screen.getByText('Most Popular')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Contact Sales' })).toBeInTheDocument();
  });
});

describe('ServicesPage template', () => {
  it('renders the header and every service card with pricing', () => {
    renderTemplate(<ServicesPage />);

    expect(screen.getByRole('heading', { level: 1, name: 'Services' })).toBeInTheDocument();
    expect(screen.getByText('Service cards with clear next steps.')).toBeInTheDocument();

    for (const title of [
      'Product design',
      'Frontend build',
      'AI features',
      'Design systems',
      'E-commerce',
      'Retainers',
    ]) {
      expect(screen.getByRole('heading', { name: title })).toBeInTheDocument();
    }
    expect(screen.getByText('From $2.5k')).toBeInTheDocument();
    expect(screen.getByText('Custom')).toBeInTheDocument();
  });

  it('gives every service a learn-more action', () => {
    renderTemplate(<ServicesPage />);

    expect(screen.getAllByRole('button', { name: 'Learn more' })).toHaveLength(6);
  });
});

describe('PortfolioPage template', () => {
  it('renders all projects and filter controls by default', () => {
    renderTemplate(<PortfolioPage />);

    expect(screen.getByRole('heading', { level: 1, name: 'Portfolio' })).toBeInTheDocument();
    expect(screen.getAllByRole('article')).toHaveLength(6);
    expect(screen.getByRole('button', { name: 'all' })).toBeInTheDocument();
    expect(screen.getByText('Northwind Analytics')).toBeInTheDocument();
  });

  it('filters the grid down to the selected tag', () => {
    renderTemplate(<PortfolioPage />);

    fireEvent.click(screen.getByRole('button', { name: 'saas' }));

    expect(screen.getAllByRole('article')).toHaveLength(2);
    expect(screen.getByText('Northwind Analytics')).toBeInTheDocument();
    expect(screen.getByText('Orbit Ops')).toBeInTheDocument();
    expect(screen.queryByText('Coral Storefront')).toBeNull();
  });

  it('restores every project when the all filter is clicked again', () => {
    renderTemplate(<PortfolioPage />);

    fireEvent.click(screen.getByRole('button', { name: 'brand' }));
    expect(screen.getAllByRole('article')).toHaveLength(2);

    fireEvent.click(screen.getByRole('button', { name: 'all' }));
    expect(screen.getAllByRole('article')).toHaveLength(6);
  });
});

describe('PricingPage template', () => {
  it('renders all plans with monthly prices by default', () => {
    renderTemplate(<PricingPage />);

    expect(screen.getByRole('heading', { level: 1, name: 'Pricing' })).toBeInTheDocument();
    for (const name of ['Starter', 'Pro', 'Business']) {
      expect(screen.getByRole('heading', { name })).toBeInTheDocument();
    }
    expect(screen.getByText('$19')).toBeInTheDocument();
    expect(screen.getByText('$49')).toBeInTheDocument();
    expect(screen.getByText('$99')).toBeInTheDocument();
    expect(screen.getAllByText('/mo')).toHaveLength(3);
  });

  it('switches every plan to yearly pricing and back', () => {
    renderTemplate(<PricingPage />);

    fireEvent.click(screen.getByRole('button', { name: 'Yearly' }));

    expect(screen.getByText('$190')).toBeInTheDocument();
    expect(screen.getByText('$490')).toBeInTheDocument();
    expect(screen.getByText('$990')).toBeInTheDocument();
    expect(screen.getAllByText('/yr')).toHaveLength(3);

    fireEvent.click(screen.getByRole('button', { name: 'Monthly' }));
    expect(screen.getByText('$19')).toBeInTheDocument();
    expect(screen.queryByText('$190')).toBeNull();
  });

  it('expands and collapses an FAQ answer', () => {
    renderTemplate(<PricingPage />);

    const faq = screen.getByRole('button', { name: 'Can I change plans later?' });
    expect(faq).toHaveAttribute('aria-expanded', 'false');

    fireEvent.click(faq);
    expect(faq).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText('Yes. Upgrade or downgrade anytime.')).toBeInTheDocument();

    fireEvent.click(faq);
    expect(faq).toHaveAttribute('aria-expanded', 'false');
  });
});

describe('ContactPage template', () => {
  it('renders contact details alongside the inquiry form', () => {
    renderTemplate(<ContactPage />);

    expect(screen.getByRole('heading', { level: 1, name: 'Contact' })).toBeInTheDocument();
    expect(screen.getByText('hello@acme.com')).toBeInTheDocument();
    expect(screen.getByText('+1 (512) 555-0142')).toBeInTheDocument();
    expect(screen.getByText('Austin, TX')).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: /Name/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Send message' })).toBeInTheDocument();
  });

  it('blocks an empty submit with inline validation errors', () => {
    renderTemplate(<ContactPage />);

    fireEvent.click(screen.getByRole('button', { name: 'Send message' }));

    expect(screen.getByText('Name is required')).toBeInTheDocument();
    expect(screen.getByText('Email is required')).toBeInTheDocument();
    expect(screen.getByText('Message is required')).toBeInTheDocument();
    expect(screen.getByText('Please accept the privacy policy')).toBeInTheDocument();
  });

  it('submits a valid inquiry and reports queued mock delivery', async () => {
    vi.useFakeTimers();
    renderTemplate(<ContactPage />);

    fireEvent.change(screen.getByRole('textbox', { name: /Name/ }), {
      target: { name: 'name', value: 'Ada Lovelace' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /Email/ }), {
      target: { name: 'email', value: 'ada@example.com' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: /Message/ }), {
      target: { name: 'message', value: 'I would like a demo of the platform.' },
    });
    fireEvent.click(screen.getByRole('checkbox'));

    fireEvent.click(screen.getByRole('button', { name: 'Send message' }));

    await act(async () => {
      await vi.advanceTimersByTimeAsync(700);
    });

    expect(screen.getByText('Message sent')).toBeInTheDocument();
    expect(screen.getByText(/Message queued/)).toBeInTheDocument();
    expect(screen.queryByText('Name is required')).toBeNull();
  });
});
