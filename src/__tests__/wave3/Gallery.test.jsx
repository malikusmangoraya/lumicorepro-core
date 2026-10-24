import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Gallery from '../../pages/Gallery';
import caseStudies from '../../data/caseStudies';

const renderGallery = () =>
  render(
    <MemoryRouter initialEntries={['/gallery']}>
      <Gallery />
    </MemoryRouter>
  );

describe('Gallery page', () => {
  it('renders the case-study header and every project card', () => {
    renderGallery();

    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading.textContent).toContain('AI-Generated');
    expect(heading.textContent).toContain('Projects');
    expect(screen.getByText('Case Studies')).toBeTruthy();
    expect(screen.getByText(/Real results from real businesses/)).toBeTruthy();
    expect(screen.getAllByRole('heading', { level: 3, hidden: true })).toHaveLength(
      caseStudies.length
    );
    expect(
      screen.getByRole('heading', {
        level: 3,
        name: 'ModiVault — Premium E-Commerce Platform',
      })
    ).toBeTruthy();
  });

  it('filters projects by industry and restores the full list with All', () => {
    renderGallery();

    fireEvent.click(screen.getByRole('button', { name: 'Healthcare' }));

    expect(screen.getAllByRole('heading', { level: 3, hidden: true })).toHaveLength(1);
    expect(
      screen.getByRole('heading', { level: 3, name: 'MedSync — Healthcare Appointment Portal' })
    ).toBeTruthy();
    expect(
      screen.queryByRole('heading', { level: 3, name: 'ModiVault — Premium E-Commerce Platform' })
    ).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'All' }));

    expect(screen.getAllByRole('heading', { level: 3, hidden: true })).toHaveLength(
      caseStudies.length
    );
  });

  it('shows client, region, stack and metrics for a project', () => {
    renderGallery();

    const cardHeading = screen.getByRole('heading', {
      level: 3,
      name: 'ModiVault — Premium E-Commerce Platform',
    });
    const card = cardHeading.parentElement.parentElement;

    expect(card.textContent).toContain('ModiVault Inc.');
    expect(card.textContent).toContain('United States');
    expect(card.textContent).toContain('+47%');
    expect(card.textContent).toContain('0.9s');
    expect(card.textContent).toContain('Stripe');
    // The old dead "View Details" button was removed (no detail route existed).
    expect(screen.queryByText('View Details')).toBeNull();
  });

  it('exposes one filter button per industry plus All', () => {
    renderGallery();

    const industries = [...new Set(caseStudies.map((study) => study.industry))].map(
      (industry) => industry.charAt(0).toUpperCase() + industry.slice(1)
    );

    expect(screen.getAllByRole('button', { name: 'All' })).toHaveLength(1);
    industries.forEach((label) => {
      expect(screen.getByRole('button', { name: label })).toBeTruthy();
    });
  });

  it('renders the closing CTA for the generator', () => {
    renderGallery();

    expect(screen.getByText('Ready to build your own?')).toBeTruthy();
    expect(screen.getByRole('button', { name: /generate your project/i })).toBeEnabled();
  });
});
