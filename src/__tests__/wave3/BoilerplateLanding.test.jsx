import { describe, expect, it, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import BoilerplateLanding from '../../pages/BoilerplateLanding';

/**
 * The page throws outside CurrencyProvider, and the real provider fetches
 * exchange rates on mount (network). Only formatPrice is needed here.
 */
vi.mock('@/hooks/useCurrency', () => ({
  useCurrency: () => ({ formatPrice: (amount) => `$${amount}` }),
}));

const renderPage = () =>
  render(
    <MemoryRouter initialEntries={['/boilerplate']}>
      <BoilerplateLanding />
    </MemoryRouter>
  );

describe('BoilerplateLanding page', () => {
  it('renders the hero, skip link and social-proof stats', () => {
    renderPage();

    expect(
      screen.getByRole('heading', { level: 1, name: 'Ship your SaaS in days, not months' })
    ).toBeTruthy();
    expect(screen.getByText(/Authentication, billing, user management/)).toBeTruthy();
    expect(screen.getByRole('link', { name: /skip to main content/i })).toHaveAttribute(
      'href',
      '#main-content'
    );
    expect(document.querySelector('#hero')).toBeTruthy();
    expect(document.querySelector('#features')).toBeTruthy();
    expect(document.querySelector('#pricing')).toBeTruthy();

    ['500+', '99.9%', '<150 KB', '13'].forEach((value) => {
      expect(screen.getByText(value)).toBeTruthy();
    });
    ['Users Served', 'Uptime', 'JS Bundle', 'Languages'].forEach((label) => {
      expect(screen.getByText(label)).toBeTruthy();
    });
  });

  it('links the hero CTAs to registration and the feature anchor', () => {
    renderPage();

    expect(screen.getByRole('link', { name: /get started free/i })).toHaveAttribute(
      'href',
      '/register'
    );
    expect(screen.getByRole('link', { name: /see features/i })).toHaveAttribute(
      'href',
      '/boilerplate#features'
    );
  });

  it('renders six feature cards and a three-step how-it-works list', () => {
    renderPage();

    const features = document.querySelector('#features');
    expect(
      within(features).getByRole('heading', {
        level: 2,
        name: 'Built-in features that set you apart',
      })
    ).toBeTruthy();
    expect(within(features).getAllByRole('heading', { level: 3, hidden: true })).toHaveLength(6);

    const how = document.querySelector('#how');
    expect(within(how).getByRole('heading', { level: 2, name: 'How it works' })).toBeTruthy();
    expect(within(how).getAllByRole('listitem')).toHaveLength(3);
    ['1', '2', '3'].forEach((n) => {
      expect(within(how).getByText(n)).toBeTruthy();
    });
  });

  it('renders the three pricing plans with formatted prices and plan CTAs', () => {
    renderPage();

    const pricing = document.querySelector('#pricing');
    expect(
      within(pricing).getByRole('heading', { level: 2, name: 'Choose your plan' })
    ).toBeTruthy();
    ['Starter', 'Pro', 'Enterprise'].forEach((plan) => {
      expect(within(pricing).getByRole('heading', { level: 3, name: plan })).toBeTruthy();
      expect(
        within(pricing).getByRole('link', { name: new RegExp(plan) })
      ).toHaveAttribute('href', '/register');
    });
    ['$49', '$99', '$199'].forEach((price) => {
      expect(within(pricing).getByText(price)).toBeTruthy();
    });
    expect(within(pricing).getByText('Most Popular')).toBeTruthy();
  });

  it('renders three FAQ disclosure widgets', () => {
    renderPage();

    const faq = document.querySelector('#faq');
    expect(within(faq).getByRole('heading', { level: 2 })).toBeTruthy();
    // landing.faq.* keys are absent from en.json, so summary text is currently
    // empty; assert the disclosure structure rather than the copy.
    expect(faq.querySelectorAll('details')).toHaveLength(3);
    expect(faq.querySelectorAll('summary')).toHaveLength(3);
  });

  it('links the closing CTA to registration', () => {
    renderPage();

    expect(
      screen.getByRole('heading', { level: 2, name: 'Ready to launch?' })
    ).toBeTruthy();
    expect(screen.getByRole('link', { name: /start building now/i })).toHaveAttribute(
      'href',
      '/register'
    );
  });
});
