import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import ContactMe from '../../templates/portfolio/ContactMe/ContactMe';
import PersonalPortfolio from '../../templates/portfolio/PersonalPortfolio/PersonalPortfolio';
import ProjectShowcase from '../../templates/portfolio/ProjectShowcase/ProjectShowcase';
import ResumeTimeline from '../../templates/portfolio/ResumeTimeline/ResumeTimeline';
import ServicesOffering from '../../templates/portfolio/ServicesOffering/ServicesOffering';

/**
 * Portfolio showcase templates: local mock data and no network. The router is
 * only needed for the TemplateShell "Templates" back link.
 */
function renderTemplate(ui) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe('ContactMe template', () => {
  it('renders the shell header, contact details, form, and open FAQ', () => {
    renderTemplate(<ContactMe />);

    expect(
      screen.getByRole('heading', { level: 1, name: "Let's Work Together" })
    ).toBeInTheDocument();
    expect(screen.getByText('Taking new projects')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Send a Message' })).toBeInTheDocument();

    expect(screen.getByText('hello@daniyal.dev')).toBeInTheDocument();
    expect(screen.getByText('+92 333 1234567')).toBeInTheDocument();
    expect(screen.getByText('F-7, Islamabad, Pakistan')).toBeInTheDocument();

    expect(screen.getByRole('textbox', { name: 'Your name' })).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: 'Email' })).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: 'Company / Project' })).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: 'Project details' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Send Message' })).toBeInTheDocument();

    const firstFaq = screen.getByRole('button', { name: 'How soon can you start?' });
    expect(firstFaq).toBeInTheDocument();
    expect(
      screen.getByText(
        'Within 1–2 weeks for most projects. Urgent rescue work can start in 48 hours.'
      )
    ).toBeInTheDocument();
  });

  it('blocks an empty submit with inline validation errors', () => {
    renderTemplate(<ContactMe />);

    fireEvent.click(screen.getByRole('button', { name: 'Send Message' }));

    expect(screen.getByText('Name is required')).toBeInTheDocument();
    expect(screen.getByText('Email is required')).toBeInTheDocument();
    expect(screen.getByText('Message is required')).toBeInTheDocument();
    expect(screen.getAllByRole('alert')).toHaveLength(3);
  });

  it('rejects a malformed email and a too-short message', () => {
    renderTemplate(<ContactMe />);

    fireEvent.change(screen.getByRole('textbox', { name: 'Your name' }), {
      target: { value: 'Ayesha Khan' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: 'Email' }), {
      target: { value: 'not-an-email' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: 'Project details' }), {
      target: { value: 'short' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Send Message' }));

    expect(screen.getByText('Enter a valid email address')).toBeInTheDocument();
    expect(screen.getByText('Message must be at least 10 characters')).toBeInTheDocument();
    expect(screen.queryByText('Name is required')).toBeNull();
  });

  it('switches the open FAQ answer', () => {
    renderTemplate(<ContactMe />);

    const secondFaq = screen.getByRole('button', { name: 'Do you work with fixed budgets?' });
    fireEvent.click(secondFaq);

    expect(
      screen.getByText(
        'Yes — fixed scope, fixed price, milestone-based payments. No surprise invoices.'
      )
    ).toBeInTheDocument();
    expect(
      screen.queryByText(
        'Within 1–2 weeks for most projects. Urgent rescue work can start in 48 hours.'
      )
    ).toBeNull();

    fireEvent.click(secondFaq);
    expect(
      screen.queryByText(
        'Yes — fixed scope, fixed price, milestone-based payments. No surprise invoices.'
      )
    ).toBeNull();
  });
});

describe('PersonalPortfolio template', () => {
  it('renders the hero identity, availability badge, and stat cards', () => {
    renderTemplate(<PersonalPortfolio />);

    expect(
      screen.getByRole('heading', { level: 1, name: 'Personal Portfolio' })
    ).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Aryan Malik' })).toBeInTheDocument();
    expect(screen.getByText('Full-Stack Developer & UI Engineer')).toBeInTheDocument();
    expect(screen.getByText('Available for work')).toBeInTheDocument();
    expect(screen.getByText('Karachi, Pakistan')).toBeInTheDocument();
    expect(screen.getByText('aryan@dev.pk')).toBeInTheDocument();

    for (const label of [
      'Years Experience',
      'Projects Delivered',
      'Happy Clients',
      'Technologies',
    ]) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
    for (const value of ['5+', '50+', '30+', '20+']) {
      expect(screen.getByText(value)).toBeInTheDocument();
    }

    for (const label of ['GitHub', 'LinkedIn', 'X (Twitter)', 'Email']) {
      expect(screen.getByRole('link', { name: label })).toBeInTheDocument();
    }
  });

  it('renders skills, experience, projects, testimonials, and the CTA', () => {
    renderTemplate(<PersonalPortfolio />);

    expect(screen.getByRole('heading', { name: 'Technical Skills' })).toBeInTheDocument();
    expect(screen.getByText('React / Next.js')).toBeInTheDocument();
    expect(screen.getByText('95%')).toBeInTheDocument();

    expect(screen.getByRole('heading', { name: 'Experience' })).toBeInTheDocument();
    expect(screen.getByText('Senior Full-Stack Developer')).toBeInTheDocument();
    expect(screen.getByText('TechNova Solutions')).toBeInTheDocument();

    expect(screen.getByRole('heading', { name: 'Featured Projects' })).toBeInTheDocument();
    for (const title of [
      'Visionary AI Platform',
      'ShopWave E-Commerce',
      'NeuroChat AI',
      'DevMetrics Dashboard',
    ]) {
      expect(screen.getByText(title)).toBeInTheDocument();
    }

    expect(screen.getByRole('heading', { name: 'Testimonials' })).toBeInTheDocument();
    expect(screen.getByText('Ahmed Siddiqui')).toBeInTheDocument();
    expect(screen.getByText('Sara Lari')).toBeInTheDocument();

    expect(
      screen.getByRole('heading', { name: "Let's Build Something Amazing" })
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Start a Project' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Say Hello' })).toBeInTheDocument();
  });

  it('filters projects to featured entries and restores them', () => {
    renderTemplate(<PersonalPortfolio />);

    fireEvent.click(screen.getByRole('button', { name: 'Featured' }));

    expect(screen.getByText('Visionary AI Platform')).toBeInTheDocument();
    expect(screen.getByText('ShopWave E-Commerce')).toBeInTheDocument();
    expect(screen.queryByText('NeuroChat AI')).toBeNull();
    expect(screen.queryByText('DevMetrics Dashboard')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'All' }));

    expect(screen.getByText('NeuroChat AI')).toBeInTheDocument();
    expect(screen.getByText('DevMetrics Dashboard')).toBeInTheDocument();
  });
});

describe('ProjectShowcase template', () => {
  it('renders the highlights strip and every project card', () => {
    renderTemplate(<ProjectShowcase />);

    expect(screen.getByRole('heading', { level: 1, name: 'Selected Work' })).toBeInTheDocument();
    expect(
      screen.getByText("A few things I've shipped — with the numbers to back them up.")
    ).toBeInTheDocument();

    for (const value of ['6+', '38', '31', '72']) {
      expect(screen.getByText(value)).toBeInTheDocument();
    }

    for (const name of [
      'Arish Grocery Mart',
      'MedQueue LHR',
      'ChaiStock Tracker',
      'FitTrack Mobile',
    ]) {
      expect(screen.getByRole('heading', { name })).toBeInTheDocument();
    }
    expect(screen.getAllByRole('img')).toHaveLength(4);
    expect(screen.getByText('+38% repeat orders in 3 months')).toBeInTheDocument();
    expect(screen.getByText('Cut front-desk calls by 60%')).toBeInTheDocument();
  });

  it('filters projects by category and restores the full grid', () => {
    renderTemplate(<ProjectShowcase />);

    fireEvent.click(screen.getByRole('button', { name: 'Healthcare' }));

    expect(screen.getByRole('heading', { name: 'MedQueue LHR' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Arish Grocery Mart' })).toBeNull();
    expect(screen.getAllByRole('img')).toHaveLength(1);

    fireEvent.click(screen.getByRole('button', { name: 'SaaS' }));

    expect(screen.getByRole('heading', { name: 'ChaiStock Tracker' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'MedQueue LHR' })).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'All' }));
    expect(screen.getAllByRole('img')).toHaveLength(4);
  });
});

describe('ResumeTimeline template', () => {
  it('renders the profile header, contacts, and experience timeline', () => {
    renderTemplate(<ResumeTimeline />);

    expect(
      screen.getByRole('heading', { level: 1, name: 'Daniyal Ahmed — Résumé' })
    ).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Daniyal Ahmed' })).toBeInTheDocument();
    expect(screen.getByText('Full-Stack Engineer & UI Builder')).toBeInTheDocument();

    for (const contact of [
      'Islamabad, Pakistan',
      'daniyal@lumi.dev',
      '+92 333 1234567',
      'linkedin.com/in/daniyal',
    ]) {
      expect(screen.getByText(contact)).toBeInTheDocument();
    }

    expect(screen.getByRole('heading', { name: 'Experience' })).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'Senior Full-Stack Engineer · TechNex' })
    ).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Full-Stack Engineer · PayPoint' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Frontend Developer · BrandCo' })).toBeInTheDocument();
    expect(screen.getByText('2024 — Present')).toBeInTheDocument();
    expect(
      screen.getByText('Cut CI time 4× with caching & parallel builds')
    ).toBeInTheDocument();
  });

  it('renders education, skills, and the open-to work CTA', () => {
    renderTemplate(<ResumeTimeline />);

    expect(screen.getByRole('heading', { name: 'Education' })).toBeInTheDocument();
    expect(screen.getByText('B.E. Software Engineering')).toBeInTheDocument();
    expect(screen.getByText('NUST — Islamabad')).toBeInTheDocument();
    expect(screen.getByText('CGPA 3.8')).toBeInTheDocument();

    expect(screen.getByRole('heading', { name: 'Skills' })).toBeInTheDocument();
    for (const group of ['Frontend', 'Backend', 'Cloud & Tooling']) {
      expect(screen.getByText(group)).toBeInTheDocument();
    }
    for (const skill of ['React', 'Postgres', 'Terraform']) {
      expect(screen.getByText(skill)).toBeInTheDocument();
    }

    expect(screen.getByText('Open to')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: "Let's Talk" })).toBeInTheDocument();
  });
});

describe('ServicesOffering template', () => {
  it('renders all service cards with prices and the default selection summary', () => {
    renderTemplate(<ServicesOffering />);

    expect(
      screen.getByRole('heading', { level: 1, name: 'Services & Rates' })
    ).toBeInTheDocument();

    for (const name of ['Landing Page', 'Web Application', 'Audit & Rescue']) {
      expect(screen.getByText(name)).toBeInTheDocument();
    }
    expect(screen.getByText('Rs 45,000')).toBeInTheDocument();
    // The card renders the price on its own; the summary renders
    // "Web Application — Rs 320,000" as one node, asserted just below.
    expect(screen.getByText('Rs 320,000')).toBeInTheDocument();
    expect(screen.getByText('Rs 90,000')).toBeInTheDocument();
    expect(screen.getByText('★ Most Requested')).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Request Quote' })).toHaveLength(3);

    expect(screen.getByText('Web Application — Rs 320,000')).toBeInTheDocument();
  });

  it('switches the selected service by click and keyboard', () => {
    renderTemplate(<ServicesOffering />);

    fireEvent.click(screen.getByText('Landing Page'));
    expect(screen.getByText('Landing Page — Rs 45,000')).toBeInTheDocument();
    expect(screen.queryByText('Web Application — Rs 320,000')).toBeNull();

    fireEvent.keyDown(screen.getByRole('button', { name: /Audit & Rescue/ }), {
      key: ' ',
      code: 'Space',
    });
    expect(screen.getByText('Audit & Rescue — Rs 90,000')).toBeInTheDocument();
    expect(screen.queryByText('Landing Page — Rs 45,000')).toBeNull();
  });

  it('renders the four-step process and booking CTA', () => {
    renderTemplate(<ServicesOffering />);

    expect(screen.getByRole('heading', { name: 'How It Works' })).toBeInTheDocument();
    for (const step of ['01 — Discover', '02 — Design', '03 — Build', '04 — Launch']) {
      expect(screen.getByText(step)).toBeInTheDocument();
    }
    expect(screen.getByRole('button', { name: 'Book a Free Call' })).toBeInTheDocument();
    expect(
      screen.getByText('Milestone payments · 7-day free ramp · IP fully yours')
    ).toBeInTheDocument();
  });
});
