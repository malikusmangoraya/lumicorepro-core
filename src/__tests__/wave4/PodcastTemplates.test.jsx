import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import AudioPlayer from '../../templates/podcast/AudioPlayer';
import GuestProfiles from '../../templates/podcast/GuestProfiles';
import LatestEpisodes from '../../templates/podcast/LatestEpisodes';
import PodcastHero from '../../templates/podcast/PodcastHero';
import ShowListings from '../../templates/podcast/ShowListings';

/**
 * Podcast showcase pages are presentational: a TemplateShell header, one hero
 * banner, and three static cards. Only a router is required for the
 * "Templates" back link.
 */
function renderTemplate(ui) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

const pages = [
  {
    name: 'AudioPlayer',
    Component: AudioPlayer,
    description: 'Podcast audio player.',
    heroLoading: 'lazy',
  },
  {
    name: 'GuestProfiles',
    Component: GuestProfiles,
    description: 'Podcast guest profiles.',
    heroLoading: 'lazy',
  },
  {
    name: 'LatestEpisodes',
    Component: LatestEpisodes,
    description: 'Latest episodes grid.',
    heroLoading: 'lazy',
  },
  {
    name: 'PodcastHero',
    Component: PodcastHero,
    description: 'Podcast hero with featured episode.',
    heroLoading: 'eager',
  },
  {
    name: 'ShowListings',
    Component: ShowListings,
    description: 'Shows and series listings.',
    heroLoading: 'lazy',
  },
];

describe.each(pages)('$name template', ({ Component, description, heroLoading }) => {
  it('renders the shell header with its category and Templates back link', () => {
    renderTemplate(<Component />);

    expect(
      screen.getByRole('heading', { level: 1, name: 'Podcast Section' })
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Templates/ })).toHaveAttribute(
      'href',
      '/templates'
    );
    // The description appears in the shell header and again in the hero overlay.
    expect(screen.getAllByText(description)).toHaveLength(2);
    // Category badge in the shell plus the hero badge.
    expect(screen.getAllByText('Podcast')).toHaveLength(2);
  });

  it('renders the hero banner image and overlay heading', () => {
    renderTemplate(<Component />);

    const hero = screen.getByRole('img', { name: 'Podcast' });
    expect(hero).toHaveClass('object-cover');
    expect(hero).toHaveAttribute('loading', heroLoading);
    expect(hero).toHaveAttribute('decoding', 'async');
    if (heroLoading === 'eager') {
      expect(hero).toHaveAttribute('fetchpriority', 'high');
    }

    expect(
      screen.getByRole('heading', { level: 2, name: 'Podcast — Podcast' })
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
