import { render, screen, waitFor } from '@testing-library/react';
import { fireEvent } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import BackToTop from '../BackToTop';
import ScrollProgress from '../ScrollProgress';

function stubScrollY(value) {
  Object.defineProperty(window, 'scrollY', { value, configurable: true, writable: true });
}

afterEach(() => {
  stubScrollY(0);
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('ScrollProgress', () => {
  it('renders a fixed, aria-hidden bar that starts empty', () => {
    const { container } = render(<ScrollProgress />);
    const track = container.firstElementChild;

    expect(track.getAttribute('aria-hidden')).toBe('true');
    expect(track.className).toContain('fixed');
    expect(track.className).toContain('top-0');

    const fill = track.firstElementChild;
    expect(fill.style.transform).toBe('scaleX(0)');
  });
});

describe('BackToTop', () => {
  it('stays hidden while the page is near the top', () => {
    stubScrollY(0);
    render(<BackToTop />);
    const button = screen.getByRole('button', { name: 'Back to top' });
    expect(button.className).toContain('invisible');
    expect(button.className).toContain('opacity-0');
  });

  it('appears once scrolled past the threshold and scrolls back on click', async () => {
    stubScrollY(600);
    const scrollTo = vi.spyOn(window, 'scrollTo').mockImplementation(() => {});

    render(<BackToTop threshold={400} />);
    const button = screen.getByRole('button', { name: 'Back to top' });

    await waitFor(() => expect(button.className).toContain('opacity-100'));
    expect(button.className).toContain('visible');

    fireEvent.click(button);
    expect(scrollTo).toHaveBeenCalledWith({ top: 0, behavior: 'smooth' });
  });

  it('uses an instant jump under prefers-reduced-motion', async () => {
    vi.stubGlobal('matchMedia', vi.fn(() => ({
      matches: true,
      addEventListener: () => {},
      removeEventListener: () => {},
    })));
    stubScrollY(600);
    const scrollTo = vi.spyOn(window, 'scrollTo').mockImplementation(() => {});

    render(<BackToTop />);
    const button = screen.getByRole('button', { name: 'Back to top' });
    await waitFor(() => expect(button.className).toContain('opacity-100'));

    fireEvent.click(button);
    expect(scrollTo).toHaveBeenCalledWith({ top: 0, behavior: 'auto' });
  });
});
