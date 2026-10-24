import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import AgentLocator from '../../templates/insurance/AgentLocator/AgentLocator';
import ClaimsProcess from '../../templates/insurance/ClaimsProcess/ClaimsProcess';
import CoverageDetails from '../../templates/insurance/CoverageDetails/CoverageDetails';
import InsuranceHero from '../../templates/insurance/InsuranceHero/InsuranceHero';
import InsurancePlans from '../../templates/insurance/InsurancePlans/InsurancePlans';

/**
 * The insurance showcase pages share one scaffold: a TemplateShell header, a
 * hero banner, and three mock cards. Each page only varies its description.
 */
function renderTemplate(ui) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

const pages = [
  { name: 'AgentLocator', Page: AgentLocator, description: 'Agent / branch locator.' },
  { name: 'ClaimsProcess', Page: ClaimsProcess, description: 'Claims process steps.' },
  { name: 'CoverageDetails', Page: CoverageDetails, description: 'Coverage comparison details.' },
  { name: 'InsuranceHero', Page: InsuranceHero, description: 'Insurance hero + quote CTA.' },
  { name: 'InsurancePlans', Page: InsurancePlans, description: 'Coverage plan cards.' },
];

describe.each(pages)('Insurance $name template', ({ Page, description }) => {
  it('renders the shell header, category badge, and hero banner', () => {
    renderTemplate(<Page />);

    expect(screen.getByRole('heading', { level: 1, name: 'Insurance Section' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Templates' })).toBeInTheDocument();

    // Shell description plus the hero's own copy of it.
    expect(screen.getAllByText(description)).toHaveLength(2);
    expect(
      screen.getByRole('heading', { level: 2, name: 'Insurance — Insurance' })
    ).toBeInTheDocument();
    expect(screen.getAllByText('Insurance')).toHaveLength(2);
    expect(screen.getByRole('img', { name: 'Insurance' })).toBeInTheDocument();
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
