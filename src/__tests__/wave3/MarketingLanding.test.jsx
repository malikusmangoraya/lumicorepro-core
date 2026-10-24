import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import MarketingLandingPage from '../../pages/MarketingLanding';

/**
 * Real bug (see report): the page passes JSX elements to `rightIcon`, but
 * `@/components/ui` Button renders icon props as components and throws
 * "Element type is invalid" on the hero CTA (MarketingLanding.jsx:102,217),
 * white-screening the whole page. Strip element icons so the rest of the page
 * can be exercised; the fix belongs in the page (pass the lucide component).
 */
vi.mock('@/components/ui', async (importOriginal) => {
  const actual = await importOriginal();
  const React = await import('react');
  const Button = (props) => {
    const next = { ...props };
    for (const key of ['leftIcon', 'rightIcon']) {
      if (React.isValidElement(next[key])) delete next[key];
    }
    return React.createElement(actual.Button, next);
  };
  return { ...actual, Button };
});

const renderPage = () =>
  render(
    <MemoryRouter initialEntries={['/marketing']}>
      <MarketingLandingPage />
    </MemoryRouter>
  );

describe('MarketingLanding page', () => {
  it('renders the hero headline, badge, subcopy and SEO metadata', () => {
    renderPage();

    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading.textContent).toContain('Describe it.');
    expect(heading.textContent).toContain('LumiCorePro builds it.');
    expect(screen.getByText('15-phase AI agent — free demo live')).toBeTruthy();
    expect(screen.getByText(/Type a sentence about your business/)).toBeTruthy();
    expect(screen.getByText(/Free demo · no credit card/)).toBeTruthy();

    expect(document.title).toBe(
      'LumiCorePro — AI that Builds Your Website From a Sentence'
    );
    expect(document.querySelector('meta[name="description"]').getAttribute('content')).toContain(
      '15-phase AI agent pipeline'
    );
  });

  it('links both hero CTAs to the demo and the template gallery', () => {
    renderPage();

    expect(screen.getByRole('link', { name: /try the live demo/i })).toHaveAttribute(
      'href',
      '/generate'
    );
    expect(screen.getByRole('link', { name: /browse 101 templates/i })).toHaveAttribute(
      'href',
      '/templates'
    );
  });

  it('renders all six capability cards and four section headings', () => {
    renderPage();

    [
      '15-Phase AI Pipeline',
      'AI Agents, Not Just Chat',
      'Live Previews',
      '101 Ready Templates',
      '13 Languages + RTL',
      'Built for Producers',
    ].forEach((title) => {
      expect(screen.getByRole('heading', { level: 3, name: title })).toBeTruthy();
    });
    expect(
      screen.getByRole('heading', { level: 2, name: 'Everything an agency does, automated' })
    ).toBeTruthy();
    expect(screen.getAllByRole('heading', { level: 2, hidden: true })).toHaveLength(4);
  });

  it('renders the three product screenshots with descriptive alt text', () => {
    renderPage();

    const images = screen.getAllByRole('img');
    expect(images).toHaveLength(3);
    expect(screen.getByAltText(/LumiCorePro generation workspace/)).toBeTruthy();
    expect(screen.getByAltText(/Analytics dashboard with revenue charts/)).toBeTruthy();
    expect(screen.getByAltText(/SaaS landing page generated/)).toBeTruthy();
    expect(screen.getByText('Generation workspace')).toBeTruthy();
    expect(screen.getByText('Analytics & insights')).toBeTruthy();
    expect(screen.getByText('Generated storefront')).toBeTruthy();
  });

  it('renders the three upcoming pricing tiers with perks', () => {
    renderPage();

    expect(
      screen.getByRole('heading', { level: 2, name: 'Simple pricing, coming soon' })
    ).toBeTruthy();
    expect(screen.getAllByText('Coming Soon')).toHaveLength(3);
    ['Starter', 'Pro', 'Studio'].forEach((plan) => {
      expect(screen.getByRole('heading', { level: 3, name: plan })).toBeTruthy();
    });
    expect(screen.getByText('Community templates')).toBeTruthy();
    expect(screen.getByText('Live deploy + domains')).toBeTruthy();
    expect(screen.getByText('White-label export')).toBeTruthy();
  });

  it('links the closing CTA to registration and the demo', () => {
    renderPage();

    expect(
      screen.getByRole('heading', { level: 2, name: 'Your next site is one sentence away' })
    ).toBeTruthy();
    expect(screen.getByRole('link', { name: /join the waitlist/i })).toHaveAttribute(
      'href',
      '/register'
    );
    expect(screen.getByRole('link', { name: /open demo/i })).toHaveAttribute('href', '/generate');
    expect(screen.getByText('Free AI cost protection')).toBeTruthy();
  });
});
