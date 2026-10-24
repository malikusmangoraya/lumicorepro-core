import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import CategoryGrid from '../../templates/marketplace/CategoryGrid';
import FeaturedVendors from '../../templates/marketplace/FeaturedVendors';
import MarketplaceHero from '../../templates/marketplace/MarketplaceHero';
import TrustBadges from '../../templates/marketplace/TrustBadges';
import VendorOnboarding from '../../templates/marketplace/VendorOnboarding';

/**
 * Marketplace showcase pages are presentational: a TemplateShell header, one
 * hero banner, and three static cards. Only a router is required for the
 * "Templates" back link.
 */
function renderTemplate(ui) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

const pages = [
  {
    name: 'CategoryGrid',
    Component: CategoryGrid,
    description: 'Product category grid.',
    heroLoading: 'lazy',
  },
  {
    name: 'FeaturedVendors',
    Component: FeaturedVendors,
    description: 'Featured vendor cards.',
    heroLoading: 'lazy',
  },
  {
    name: 'MarketplaceHero',
    Component: MarketplaceHero,
    description: 'Marketplace hero.',
    heroLoading: 'eager',
  },
  {
    name: 'TrustBadges',
    Component: TrustBadges,
    description: 'Trust / safety badges.',
    heroLoading: 'lazy',
  },
  {
    name: 'VendorOnboarding',
    Component: VendorOnboarding,
    description: 'Vendor onboarding steps.',
    heroLoading: 'lazy',
  },
];

describe.each(pages)('$name template', ({ Component, description, heroLoading }) => {
  it('renders the shell header with its category and Templates back link', () => {
    renderTemplate(<Component />);

    expect(
      screen.getByRole('heading', { level: 1, name: 'Marketplace Section' })
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Templates/ })).toHaveAttribute(
      'href',
      '/templates'
    );
    // The description appears in the shell header and again in the hero overlay.
    expect(screen.getAllByText(description)).toHaveLength(2);
    // Category badge in the shell plus the hero badge.
    expect(screen.getAllByText('Marketplace')).toHaveLength(2);
  });

  it('renders the hero banner image and overlay heading', () => {
    renderTemplate(<Component />);

    const hero = screen.getByRole('img', { name: 'Marketplace' });
    expect(hero).toHaveClass('object-cover');
    expect(hero).toHaveAttribute('loading', heroLoading);
    expect(hero).toHaveAttribute('decoding', 'async');
    if (heroLoading === 'eager') {
      expect(hero).toHaveAttribute('fetchpriority', 'high');
    }

    expect(
      screen.getByRole('heading', { level: 2, name: 'Marketplace — Marketplace' })
    ).toBeInTheDocument();
  });

  it('renders three cards with tags, ratings, and learn-more actions', () => {
    renderTemplate(<Component />);

    expect(screen.getAllByRole('heading', { level: 3 }).map((h) => h.textContent)).toEqual([
      'Item One',
      'Item Two',
      'Item Three',
    ]);
    for (const copy of [
      'Short description for the first item.',
      'Short description for the second item.',
      'Short description for the third item.',
    ]) {
      expect(screen.getByText(copy)).toBeInTheDocument();
    }

    expect(screen.getByText('Popular')).toBeInTheDocument();
    expect(screen.getByText('New')).toBeInTheDocument();
    // Two shells badges plus the Popular/New tags; the third card has no tag.
    expect(screen.getAllByRole('status')).toHaveLength(4);

    expect(screen.getAllByText('4.8 rating')).toHaveLength(3);
    expect(screen.getAllByRole('button', { name: 'Learn More' })).toHaveLength(3);
  });
});
