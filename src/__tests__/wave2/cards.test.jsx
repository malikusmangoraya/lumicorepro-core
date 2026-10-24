import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TrendingUp, Zap } from 'lucide-react';
import StatsCard from '../../components/ui/StatsCard';
import FeatureCard from '../../components/ui/FeatureCard';

afterEach(() => {
  vi.restoreAllMocks();
});

describe('StatsCard', () => {
  it('renders title, value and an upward trend with the reported change', () => {
    render(
      <StatsCard
        title="Monthly revenue"
        value="$48,200"
        change={12.5}
        changeLabel="vs last month"
        trend="up"
      />
    );

    expect(screen.getByText('Monthly revenue')).toBeTruthy();
    expect(screen.getByText('$48,200')).toBeTruthy();
    expect(screen.getByText(/↑/)).toHaveTextContent('↑ 12.5%');
    expect(screen.getByText('vs last month')).toBeTruthy();
  });

  it('shows a downward trend without a negative sign duplicating the arrow', () => {
    render(<StatsCard title="Churn" value="2.1%" change={-8} trend="down" />);
    expect(screen.getByText(/↓/)).toHaveTextContent('↓ 8%');
  });

  it('renders a forwardRef icon component and forwards clicks to the card', () => {
    const onClick = vi.fn();
    const { container } = render(
      <StatsCard title="Active" value="1,204" icon={TrendingUp} onClick={onClick} />
    );

    const card = container.firstElementChild;
    expect(card.querySelector('svg')).not.toBeNull();
    fireEvent.click(card);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('renders children content when supplied', () => {
    render(
      <StatsCard title="Storage" value="82%">
        <p>Upgrade to add more space</p>
      </StatsCard>
    );
    expect(screen.getByText('Upgrade to add more space')).toBeTruthy();
  });
});

describe('FeatureCard', () => {
  it('renders its heading, description and badge in a level-3 heading', () => {
    render(
      <FeatureCard
        title="Edge delivery"
        description="Cached in 300+ locations."
        badge="New"
      />
    );

    expect(screen.getByRole('heading', { level: 3, name: 'Edge delivery' })).toBeTruthy();
    expect(screen.getByText('Cached in 300+ locations.')).toBeTruthy();
    expect(screen.getByText('New')).toBeTruthy();
  });

  it('applies the requested variant and icon size classes', () => {
    const { container } = render(
      <FeatureCard title="Glass" description="Frosted." variant="glass" icon={Zap} iconSize="lg" />
    );

    const card = container.firstElementChild;
    expect(card.className).toContain('backdrop-blur-xl');
    expect(card.querySelector('svg')).not.toBeNull();
    expect(card.querySelector('.rounded-2xl')).not.toBeNull();
  });

  it('renders arbitrary children content', () => {
    render(
      <FeatureCard title="Checklist" description="Included">
        <ul>
          <li>SSO</li>
          <li>Audit logs</li>
        </ul>
      </FeatureCard>
    );

    expect(screen.getByRole('list')).toBeTruthy();
    expect(screen.getAllByRole('listitem')).toHaveLength(2);
  });

  it('does not render the Learn more affordance when there is no destination', () => {
    render(<FeatureCard title="Static" description="No link" />);
    expect(screen.queryByText('Learn more')).toBeNull();
  });
});
