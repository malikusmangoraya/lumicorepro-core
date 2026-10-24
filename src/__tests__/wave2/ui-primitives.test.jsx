import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Bell } from 'lucide-react';
import Badge from '../../components/ui/Badge';
import Alert from '../../components/ui/Alert';
import Spinner from '../../components/ui/Spinner';
import Loading from '../../components/ui/Loading';
import Skeleton from '../../components/ui/Skeleton';

afterEach(() => {
  vi.restoreAllMocks();
});

describe('Badge', () => {
  it('renders as a status by default with the requested variant and size', () => {
    render(
      <Badge variant="success" size="sm">
        In stock
      </Badge>
    );

    const badge = screen.getByRole('status');
    expect(badge).toHaveTextContent('In stock');
    expect(badge.className).toContain('bg-green-100');
    expect(badge.className).toContain('text-xs');
  });

  it('becomes a keyboard-operable button when onClick is supplied', () => {
    const onClick = vi.fn();
    render(<Badge onClick={onClick}>Filter</Badge>);

    const badge = screen.getByRole('button', { name: 'Filter' });
    expect(badge).toHaveAttribute('tabindex', '0');

    fireEvent.keyDown(badge, { key: 'Enter' });
    fireEvent.keyDown(badge, { key: ' ' });
    expect(onClick).toHaveBeenCalledTimes(2);
  });

  it('renders a decorative dot that is hidden from assistive tech', () => {
    const { container } = render(<Badge dot>Live</Badge>);
    const dot = container.querySelector('[aria-hidden="true"].rounded-full');
    expect(dot).not.toBeNull();
    expect(dot.className).toContain('h-1.5');
  });

  it('removes itself without triggering the badge onClick', () => {
    const onClick = vi.fn();
    const onRemove = vi.fn();
    render(
      <Badge removable onClick={onClick} onRemove={onRemove}>
        Draft
      </Badge>
    );

    fireEvent.click(screen.getByRole('button', { name: 'Remove badge' }));

    expect(onRemove).toHaveBeenCalledTimes(1);
    expect(onClick).not.toHaveBeenCalled();
  });
});

describe('Alert', () => {
  it('exposes an alert role with the variant styling and title', () => {
    render(
      <Alert variant="danger" title="Payment failed">
        Card was declined
      </Alert>
    );

    const alert = screen.getByRole('alert');
    expect(alert).toHaveTextContent('Payment failed');
    expect(alert).toHaveTextContent('Card was declined');
    expect(alert.className).toContain('bg-red-50');
  });

  it('renders a forwardRef icon component without crashing', () => {
    // lucide icons are forwardRef objects, not functions — the same class of
    // crash documented for GlassButton in AGENTS.md §4.
    const { container } = render(<Alert icon={Bell}>Heads up</Alert>);
    expect(screen.getByRole('alert')).toHaveTextContent('Heads up');
    expect(container.querySelector('svg')).not.toBeNull();
  });

  it('dismisses via onDismiss and falls back to onClose', () => {
    const onDismiss = vi.fn();
    const onClose = vi.fn();

    const { unmount } = render(
      <Alert dismissible onDismiss={onDismiss} onClose={onClose}>
        First
      </Alert>
    );
    fireEvent.click(screen.getByRole('button', { name: 'Dismiss alert' }));
    expect(onDismiss).toHaveBeenCalledTimes(1);
    expect(onClose).not.toHaveBeenCalled();
    unmount();

    render(
      <Alert dismissible onClose={onClose}>
        Second
      </Alert>
    );
    fireEvent.click(screen.getByRole('button', { name: 'Dismiss alert' }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('omits the dismiss control unless dismissible', () => {
    render(<Alert>Static notice</Alert>);
    expect(screen.queryByRole('button', { name: 'Dismiss alert' })).toBeNull();
  });
});

describe('Spinner', () => {
  it('announces itself as a status with a default accessible name', () => {
    render(<Spinner />);
    const status = screen.getByRole('status', { name: 'Loading...' });
    expect(status.querySelector('.animate-spin')).not.toBeNull();
  });

  it('supports a custom label, size and colour', () => {
    render(<Spinner size="xl" color="white" label="Syncing data" />);
    const status = screen.getByRole('status', { name: 'Syncing data' });
    const ring = status.querySelector('.animate-spin');

    expect(ring.className).toContain('h-12');
    expect(ring.className).toContain('border-t-white');
  });
});

describe('Loading', () => {
  it('renders a polite live region with the loading text', () => {
    render(<Loading text="Fetching projects" />);
    // The outer wrapper owns aria-live; the Spinner adds a nested status too.
    const wrapper = screen.getAllByRole('status')[0];
    expect(wrapper).toHaveAttribute('aria-live', 'polite');
    expect(screen.getByText('Fetching projects')).toBeTruthy();
  });

  it('covers the viewport in fullScreen mode', () => {
    const { container } = render(<Loading fullScreen text="Booting" />);
    const wrapper = container.firstElementChild;
    expect(wrapper.className).toContain('fixed');
    expect(wrapper.className).toContain('inset-0');
  });
});

describe('Skeleton', () => {
  it('is a status with a variant shape and shimmer by default', () => {
    render(<Skeleton variant="circle" />);
    const skeleton = screen.getByRole('status', { name: 'Loading...' });
    expect(skeleton.className).toContain('h-10');
    expect(skeleton.className).toContain('rounded-full');
    expect(skeleton.className).toContain('animate-shimmer');
  });

  it('switches to a pulse when shimmer is disabled', () => {
    render(<Skeleton variant="rect" shimmer={false} />);
    const skeleton = screen.getByRole('status', { name: 'Loading...' });
    expect(skeleton.className).toContain('animate-pulse');
    expect(skeleton.className).not.toContain('animate-shimmer');
  });
});
