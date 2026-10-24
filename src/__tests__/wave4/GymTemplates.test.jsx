import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import ClassSchedule from '../../templates/gym/ClassSchedule/ClassSchedule';
import GymHero from '../../templates/gym/GymHero/GymHero';
import MembershipPlans from '../../templates/gym/MembershipPlans/MembershipPlans';
import SuccessStories from '../../templates/gym/SuccessStories/SuccessStories';
import TrainerProfiles from '../../templates/gym/TrainerProfiles/TrainerProfiles';

/**
 * The gym showcase pages share one scaffold: a TemplateShell header, a hero
 * banner, and three mock cards. Each page only varies its description.
 */
function renderTemplate(ui) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

const pages = [
  { name: 'ClassSchedule', Page: ClassSchedule, description: 'Weekly class schedule.' },
  { name: 'GymHero', Page: GymHero, description: 'Gym hero with membership CTA.' },
  { name: 'MembershipPlans', Page: MembershipPlans, description: 'Membership pricing plans.' },
  { name: 'SuccessStories', Page: SuccessStories, description: 'Member success stories.' },
  { name: 'TrainerProfiles', Page: TrainerProfiles, description: 'Certified trainer profiles.' },
];

describe.each(pages)('Gym $name template', ({ Page, description }) => {
  it('renders the shell header, category badge, and hero banner', () => {
    renderTemplate(<Page />);

    expect(screen.getByRole('heading', { level: 1, name: 'Gym Section' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Templates' })).toBeInTheDocument();

    // Shell description plus the hero's own copy of it.
    expect(screen.getAllByText(description)).toHaveLength(2);
    expect(screen.getByRole('heading', { level: 2, name: 'Gym — Gym' })).toBeInTheDocument();
    expect(screen.getAllByText('Gym')).toHaveLength(2);
    expect(screen.getByRole('img', { name: 'Gym' })).toBeInTheDocument();
  });

  it('renders the three mock cards with tags and descriptions', () => {
    renderTemplate(<Page />);

    for (const title of ['Item One', 'Item Two', 'Item Three']) {
      expect(screen.getByRole('heading', { name: title })).toBeInTheDocument();
    }
    expect(screen.getByText('Short description for the first item.')).toBeInTheDocument();
    expect(screen.getByText('Short description for the second item.')).toBeInTheDocument();
    expect(screen.getByText('Short description for the third item.')).toBeInTheDocument();

    const headerFor = (title) => screen.getByRole('heading', { name: title }).parentElement;
    expect(within(headerFor('Item One')).getByText('Popular')).toBeInTheDocument();
    expect(within(headerFor('Item Two')).getByText('New')).toBeInTheDocument();
    // The third card intentionally has no tag.
    expect(within(headerFor('Item Three')).queryByRole('status')).toBeNull();
  });

  it('shows a rating and an enabled learn-more action on every card', () => {
    renderTemplate(<Page />);

    expect(screen.getAllByText('4.8 rating')).toHaveLength(3);

    const buttons = screen.getAllByRole('button', { name: 'Learn More' });
    expect(buttons).toHaveLength(3);
    for (const button of buttons) {
      expect(button).toBeEnabled();
    }
  });
});
