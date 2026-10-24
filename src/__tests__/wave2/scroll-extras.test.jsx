import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ScrollProgress from '../../components/ui/ScrollProgress';
import BackToTop from '../../components/ui/BackToTop';
import Tooltip from '../../components/ui/Tooltip';

function stubScroll({ scrollHeight = 2000, clientHeight = 1000, scrollY = 0 } = {}) {
  Object.defineProperty(document.documentElement, 'scrollHeight', {
    value: scrollHeight,
    configurable: true,
  });
  Object.defineProperty(document.documentElement, 'clientHeight', {
    value: clientHeight,
    configurable: true,
  });
  Object.defineProperty(window, 'scrollY', { value: scrollY, configurable: true, writable: true });
}

afterEach(() => {
  Object.defineProperty(window, 'scrollY', { value: 0, configurable: true, writable: true });
  vi.restoreAllMocks();
});

describe('ScrollProgress', () => {
  it('fills proportionally to the scrollable distance', async () => {
    stubScroll({ scrollHeight: 2000, clientHeight: 1000, scrollY: 500 });
    const { container } = render(<ScrollProgress />);
    const fill = container.firstElementChild.firstElementChild;

    await waitFor(() => expect(fill.style.transform).toBe('scaleX(0.5)'));

    Object.defineProperty(window, 'scrollY', { value: 1500, configurable: true, writable: true });
    fireEvent.scroll(window);

    await waitFor(() => expect(fill.style.transform).toBe('scaleX(1)'));
  });

  it('removes its scroll and resize listeners on unmount', () => {
    const removeSpy = vi.spyOn(window, 'removeEventListener');
    const { unmount } = render(<ScrollProgress />);

    unmount();

    expect(removeSpy).toHaveBeenCalledWith('scroll', expect.any(Function));
    expect(removeSpy).toHaveBeenCalledWith('resize', expect.any(Function));
  });
});

describe('BackToTop scroll listener', () => {
  it('reacts to scroll events fired after mount', async () => {
    stubScroll({ scrollY: 0 });
    render(<BackToTop threshold={400} />);
    const button = screen.getByRole('button', { name: 'Back to top' });
    expect(button.className).toContain('invisible');

    Object.defineProperty(window, 'scrollY', { value: 900, configurable: true, writable: true });
    fireEvent.scroll(window);

    await waitFor(() => expect(button.className).toContain('opacity-100'));

    Object.defineProperty(window, 'scrollY', { value: 100, configurable: true, writable: true });
    fireEvent.scroll(window);

    await waitFor(() => expect(button.className).toContain('opacity-0'));
  });

  it('unregisters its scroll listener on unmount', () => {
    const removeSpy = vi.spyOn(window, 'removeEventListener');
    const { unmount } = render(<BackToTop />);

    unmount();

    expect(removeSpy).toHaveBeenCalledWith('scroll', expect.any(Function));
  });
});

describe('Tooltip placement', () => {
  it('applies the requested position classes', () => {
    render(
      <Tooltip content="More actions" open position="left">
        <button type="button">Trigger</button>
      </Tooltip>
    );

    const tooltip = screen.getByRole('tooltip');
    expect(tooltip.className).toContain('right-full');
    expect(tooltip.className).toContain('top-1/2');
  });

  it('renders content as text rather than injecting markup', () => {
    render(
      <Tooltip content="<b>Saved</b>" open>
        <button type="button">Trigger</button>
      </Tooltip>
    );

    expect(screen.getByRole('tooltip')).toHaveTextContent('<b>Saved</b>');
    expect(screen.getByRole('tooltip').querySelector('b')).toBeNull();
  });
});
