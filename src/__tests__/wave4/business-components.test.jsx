import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import PricingCard from '../../components/business/PricingCard';
import PricingGrid from '../../components/business/PricingGrid';
import FAQItem from '../../components/business/FAQItem';
import FeatureGrid from '../../components/business/FeatureGrid';
import Hero from '../../components/business/Hero';

afterEach(() => {
  vi.restoreAllMocks();
});

describe('PricingCard', () => {
  it('renders the plan name, price, period, description and feature list', () => {
    render(
      <PricingCard
        name="Pro"
        price="$29"
        period="/mo"
        description="For growing teams"
        features={['Unlimited projects', 'Priority support']}
        highlighted
      />
    );

    expect(screen.getByRole('heading', { level: 3, name: 'Pro' })).toBeTruthy();
    expect(screen.getByText('$29')).toBeTruthy();
    expect(screen.getByText('/mo')).toBeTruthy();
    expect(screen.getByText('For growing teams')).toBeTruthy();
    expect(screen.getByText('Unlimited projects')).toBeTruthy();
    expect(screen.getAllByRole('listitem')).toHaveLength(2);
    // Highlighted plans are flagged with a "Popular" ribbon.
    expect(screen.getByText('Popular')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Choose Pro plan' })).toHaveTextContent(
      'Choose plan'
    );
  });

  it('uses the neutral CTA and reports the plan payload back to onSelect', () => {
    const onSelect = vi.fn();
    render(<PricingCard name="Starter" price="$0" period="/mo" onSelect={onSelect} />);

    expect(screen.queryByText('Popular')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Choose Starter plan' }));

    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'Starter',
        price: '$0',
        period: '/mo',
        features: [],
        highlighted: false,
      }),
      expect.objectContaining({ type: 'click' })
    );
  });

  it('applies the animation delay, custom class and pass-through props', () => {
    const { container } = render(
      <PricingCard name="Team" price="$99" animationDelay={150} className="my-tier" data-testid="tier" />
    );

    const card = screen.getByTestId('tier');
    expect(card).toBe(container.firstElementChild);
    expect(card.className).toContain('my-tier');
    expect(card.style.transitionDelay).toBe('150ms');
  });

  it('omits the description, period and ribbon when they are not supplied', () => {
    render(<PricingCard name="Free" price="$0" />);

    const card = screen.getByRole('heading', { level: 3, name: 'Free' }).parentElement;
    expect(card.querySelectorAll('p')).toHaveLength(0);
    expect(card.querySelectorAll('li')).toHaveLength(0);
    expect(screen.getByRole('button', { name: 'Choose Free plan' })).toHaveTextContent(
      'Get started'
    );
  });
});

describe('PricingGrid', () => {
  const buildPlans = () =>
    Array.from({ length: 5 }, (_, index) => ({
      id: `plan-${index}`,
      name: `Plan ${index + 1}`,
      price: `$${index}`,
    }));

  it('renders a card per plan and cycles the animation delay', () => {
    const { container } = render(<PricingGrid plans={buildPlans()} />);

    expect(screen.getByRole('heading', { level: 3, name: 'Plan 1' })).toBeTruthy();
    expect(screen.getByRole('heading', { level: 3, name: 'Plan 5' })).toBeTruthy();
    expect(container.querySelectorAll('li')).toHaveLength(0);

    const delays = [...container.firstElementChild.children].map(
      (card) => card.style.transitionDelay
    );
    expect(delays).toEqual(['0ms', '100ms', '200ms', '300ms', '0ms']);
  });

  it('calls the plan handler first, then onPlanSelect with the plan and index', () => {
    const planSelect = vi.fn();
    const onPlanSelect = vi.fn();
    const plans = [{ id: 'basic', name: 'Basic', price: '$9', onSelect: planSelect }];

    render(<PricingGrid plans={plans} onPlanSelect={onPlanSelect} />);
    fireEvent.click(screen.getByRole('button', { name: 'Choose Basic plan' }));

    expect(planSelect).toHaveBeenCalledTimes(1);
    expect(planSelect).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'Basic', price: '$9' }),
      expect.objectContaining({ type: 'click' })
    );
    expect(onPlanSelect).toHaveBeenCalledTimes(1);
    expect(onPlanSelect.mock.calls[0][0]).toBe(plans[0]);
    expect(onPlanSelect.mock.calls[0][1]).toBe(0);
  });

  it('maps the columns prop to the grid classes and renders nothing for no plans', () => {
    const { container, rerender } = render(<PricingGrid plans={[]} columns={4} />);
    const grid = container.firstElementChild;

    expect(grid.children).toHaveLength(0);
    expect(grid.className).toContain('lg:grid-cols-4');
    expect(grid.className).toContain('gap-8');

    rerender(<PricingGrid plans={[{ id: 'a', name: 'A', price: '1' }]} />);
    expect(container.firstElementChild.className).toContain('lg:grid-cols-3');
  });
});

describe('FAQItem', () => {
  it('toggles the answer and reports every state change', () => {
    const onToggle = vi.fn();
    const onChange = vi.fn();
    render(
      <FAQItem
        question="Can I cancel?"
        answer="Anytime, from the dashboard."
        onToggle={onToggle}
        onChange={onChange}
      />
    );

    const trigger = screen.getByRole('button', { name: /Can I cancel\?/ });
    expect(trigger).toHaveAttribute('aria-expanded', 'false');

    fireEvent.click(trigger);
    expect(trigger).toHaveAttribute('aria-expanded', 'true');
    expect(onToggle).toHaveBeenLastCalledWith(true);
    expect(onChange).toHaveBeenLastCalledWith(true);

    fireEvent.click(trigger);
    expect(trigger).toHaveAttribute('aria-expanded', 'false');
    expect(onToggle).toHaveBeenLastCalledWith(false);
  });

  it('starts open and rotates the chevron when defaultOpen is set', () => {
    const { container } = render(
      <FAQItem question="Shipping?" answer="Worldwide." defaultOpen />
    );

    expect(screen.getByRole('button', { name: /Shipping\?/ })).toHaveAttribute(
      'aria-expanded',
      'true'
    );
    const chevron = container.querySelector('svg');
    expect(chevron.getAttribute('class')).toContain('rotate-180');
    expect(screen.getByText('Worldwide.')).toBeTruthy();
  });

  it('keeps the panel open when the parent controls the open state', () => {
    const onToggle = vi.fn();
    render(
      <FAQItem question="Controlled?" answer="Yes." open onToggle={onToggle} />
    );

    const trigger = screen.getByRole('button', { name: /Controlled\?/ });
    fireEvent.click(trigger);

    expect(trigger).toHaveAttribute('aria-expanded', 'true');
    expect(onToggle).toHaveBeenCalledWith(false);
  });

  it('applies animation, delay and custom classes at the root', () => {
    const { container } = render(
      <FAQItem question="Styled?" answer="Sure." animate="fade-up" animationDelay={200} className="faq-row" />
    );

    const root = container.firstElementChild;
    expect(root.className).toContain('faq-row');
    expect(root.className).toContain('animate-fade-in-up');
    expect(root.className).toContain('delay-200');
  });
});

describe('FeatureGrid', () => {
  it('renders the default six features under the default heading', () => {
    const { container } = render(<FeatureGrid />);

    expect(screen.getByRole('heading', { level: 2, name: 'Everything you need' })).toBeTruthy();
    expect(screen.getByText('Powerful capabilities included with every project.')).toBeTruthy();
    expect(container.querySelectorAll('article')).toHaveLength(6);
    expect(screen.getByRole('heading', { level: 3, name: 'Lightning fast' })).toBeTruthy();
    expect(screen.getByText('⚡')).toBeTruthy();
  });

  it('renders custom features with an emoji fallback and the requested column count', () => {
    const { container } = render(
      <FeatureGrid
        title="Why us"
        subtitle=""
        columns={2}
        features={[
          { title: 'Audit logs', body: 'Every action recorded.' },
          { title: 'SSO', body: 'SAML and OIDC.', emoji: '🔑' },
        ]}
      />
    );

    expect(screen.getByRole('heading', { level: 3, name: 'Audit logs' })).toBeTruthy();
    expect(screen.getByText('Every action recorded.')).toBeTruthy();
    expect(screen.getByText('🔑')).toBeTruthy();
    expect(screen.getByText('✦')).toBeTruthy();

    const grid = container.querySelector('.grid');
    expect(grid.className).toContain('sm:grid-cols-2');
    expect(grid.className).not.toContain('lg:grid-cols-3');
    expect(
      screen.queryByText('Powerful capabilities included with every project.')
    ).toBeNull();
  });

  it('falls back to three columns for an unsupported value and keeps the section class', () => {
    const { container } = render(
      <FeatureGrid columns={9} className="features-dark" features={[{ title: 'One' }]} />
    );

    const section = container.firstElementChild;
    expect(section.tagName).toBe('SECTION');
    expect(section.className).toContain('features-dark');
    // A missing body/emoji must not crash the card.
    expect(container.querySelector('article')).toBeTruthy();
    expect(container.querySelector('.grid').className).toContain('lg:grid-cols-3');
  });
});

describe('Hero', () => {
  it('renders the badge, headline, highlight and subtitle', () => {
    render(<Hero image={null} />);

    expect(screen.getByText('Trusted by 2,000+ teams')).toBeTruthy();
    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading).toHaveTextContent('Build something extraordinary');
    expect(heading).toHaveTextContent('today.');
    expect(screen.getByText(/A complete platform that turns ambitious ideas/)).toBeTruthy();
    expect(screen.queryByRole('button')).toBeNull();
  });

  it('only renders CTAs when handlers are supplied and fires them on click', () => {
    const onPrimary = vi.fn();
    const onSecondary = vi.fn();
    render(<Hero image={null} onPrimary={onPrimary} onSecondary={onSecondary} />);

    fireEvent.click(screen.getByRole('button', { name: 'Get started' }));
    fireEvent.click(screen.getByRole('button', { name: 'Watch demo' }));

    expect(onPrimary).toHaveBeenCalledTimes(1);
    expect(onSecondary).toHaveBeenCalledTimes(1);
  });

  it('renders only the secondary CTA when onPrimary is missing', () => {
    const onSecondary = vi.fn();
    render(<Hero image={null} onSecondary={onSecondary} />);

    expect(screen.queryByRole('button', { name: 'Get started' })).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Watch demo' }));
    expect(onSecondary).toHaveBeenCalledTimes(1);
  });

  it('renders a supplied image with its alt text and hides it when image is null', () => {
    const { container, rerender } = render(
      <Hero image="https://images.example.com/team.jpg" imageAlt="Team at work" />
    );

    const image = screen.getByAltText('Team at work');
    expect(image).toHaveAttribute('src', 'https://images.example.com/team.jpg');
    expect(image).toHaveAttribute('loading', 'lazy');

    rerender(<Hero image={null} />);
    expect(container.querySelector('img')).toBeNull();
  });

  it('drops the badge on an empty string and left-aligns when requested', () => {
    const { container } = render(<Hero image={null} badge="" align="left" />);

    expect(screen.queryByText('Trusted by 2,000+ teams')).toBeNull();
    const wrapper = container.querySelector('section > div.relative');
    expect(wrapper.className).not.toContain('items-center');
    expect(wrapper.className).not.toContain('text-center');
  });
});
