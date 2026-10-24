import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import FeaturedTopics from '../../templates/newsletter/FeaturedTopics';
import IssueArchive from '../../templates/newsletter/IssueArchive';
import NewsletterHero from '../../templates/newsletter/NewsletterHero';
import PreviousIssue from '../../templates/newsletter/PreviousIssue';
import SubscribeForm from '../../templates/newsletter/SubscribeForm';

/**
 * Newsletter showcase pages are presentational: a TemplateShell header, one
 * hero banner, and three static cards. Only a router is required for the
 * "Templates" back link.
 */
function renderTemplate(ui) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

const pages = [
  {
    name: 'FeaturedTopics',
    Component: FeaturedTopics,
    description: 'Topics covered this week.',
  },
  {
    name: 'IssueArchive',
    Component: IssueArchive,
    description: 'Past issue archive.',
  },
  {
    name: 'NewsletterHero',
    Component: NewsletterHero,
    description: 'Newsletter hero + subscribe.',
  },
  {
    name: 'PreviousIssue',
    Component: PreviousIssue,
    description: 'Previous issue preview.',
  },
  {
    name: 'SubscribeForm',
    Component: SubscribeForm,
    description: 'Email subscribe form.',
  },
];

describe.each(pages)('$name template', ({ Component, description }) => {
  it('renders the shell header with its category and Templates back link', () => {
    renderTemplate(<Component />);

    expect(
      screen.getByRole('heading', { level: 1, name: 'Newsletter Section' })
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Templates/ })).toHaveAttribute(
      'href',
      '/templates'
    );
    // The description appears in the shell header and again in the hero overlay.
    expect(screen.getAllByText(description)).toHaveLength(2);
    // Category badge in the shell plus the hero badge.
    expect(screen.getAllByText('Newsletter')).toHaveLength(2);
  });

  it('renders the hero banner image and overlay heading', () => {
    renderTemplate(<Component />);

    const hero = screen.getByRole('img', { name: 'Newsletter' });
    expect(hero).toHaveClass('object-cover');
    expect(hero).toHaveAttribute('loading', 'lazy');
    expect(hero).toHaveAttribute('decoding', 'async');

    expect(
      screen.getByRole('heading', { level: 2, name: 'Newsletter — Newsletter' })
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
    // Two shell badges plus the Popular/New tags; the third card has no tag.
    expect(screen.getAllByRole('status')).toHaveLength(4);

    expect(screen.getAllByText('4.8 rating')).toHaveLength(3);
    expect(screen.getAllByRole('button', { name: 'Learn More' })).toHaveLength(3);
  });
});
