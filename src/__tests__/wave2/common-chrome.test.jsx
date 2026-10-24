import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import SkipToContent from '../../components/common/SkipToContent';
import PageSkeleton from '../../components/common/PageSkeleton';
import ErrorBoundary from '../../components/common/ErrorBoundary';
import LazyImage from '../../components/common/LazyImage';

describe('SkipToContent', () => {
  it('is the first-focusable link to the main landmark', () => {
    render(<SkipToContent />);
    const link = screen.getByRole('link', { name: 'Skip to main content' });

    expect(link).toHaveAttribute('href', '#main-content');
    expect(link.className).toContain('sr-only');
    expect(link.className).toContain('focus:not-sr-only');
  });

  it('merges a custom className', () => {
    render(<SkipToContent className="custom-skip" />);
    expect(screen.getByRole('link').className).toContain('custom-skip');
  });
});

describe('PageSkeleton', () => {
  it('announces loading politely to assistive tech', () => {
    render(<PageSkeleton />);
    const region = screen.getByRole('status');

    expect(region).toHaveAttribute('aria-live', 'polite');
    expect(screen.getByText('Loading…')).toBeTruthy();
    expect(region.className).toContain('animate-pulse');
  });

  it('renders six placeholder cards in a responsive grid', () => {
    const { container } = render(<PageSkeleton />);
    const cards = container.querySelectorAll('.grid > div');

    expect(cards).toHaveLength(6);
    expect(container.querySelector('.grid').className).toContain('sm:grid-cols-2');
  });
});

describe('ErrorBoundary', () => {
  let consoleError;

  beforeEach(() => {
    consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleError.mockRestore();
  });

  it('renders its children when nothing throws', () => {
    render(
      <MemoryRouter>
        <ErrorBoundary>
          <p>Healthy subtree</p>
        </ErrorBoundary>
      </MemoryRouter>
    );

    expect(screen.getByText('Healthy subtree')).toBeTruthy();
  });

  it('shows a friendly fallback with the error message, retry and home link', () => {
    const Boom = () => {
      throw new Error('Boom while rendering');
    };

    render(
      <MemoryRouter>
        <ErrorBoundary>
          <Boom />
        </ErrorBoundary>
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { name: 'Something went wrong' })).toBeTruthy();
    expect(screen.getByText('Boom while rendering')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Try again' })).toBeTruthy();
    expect(screen.getByRole('link', { name: 'Go home' })).toHaveAttribute('href', '/');
  });

  it('recovers the subtree when Try again succeeds', () => {
    let shouldThrow = true;
    const Flaky = () => {
      if (shouldThrow) throw new Error('Transient failure');
      return <p>Recovered content</p>;
    };

    render(
      <MemoryRouter>
        <ErrorBoundary>
          <Flaky />
        </ErrorBoundary>
      </MemoryRouter>
    );

    expect(screen.getByText('Transient failure')).toBeTruthy();
    shouldThrow = false;
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }));

    expect(screen.getByText('Recovered content')).toBeTruthy();
    expect(screen.queryByText('Something went wrong')).toBeNull();
  });
});

describe('LazyImage', () => {
  it('renders a lazily decoded image with its alt text and a placeholder', () => {
    const { container } = render(
      <LazyImage src="https://cdn.example/hero.webp" alt="Dashboard preview" />
    );

    const img = screen.getByRole('img', { name: 'Dashboard preview' });
    expect(img).toHaveAttribute('src', 'https://cdn.example/hero.webp');
    expect(img).toHaveAttribute('loading', 'lazy');
    expect(img).toHaveAttribute('decoding', 'async');
    expect(img.className).toContain('opacity-0');
    expect(container.querySelector('.animate-pulse')).not.toBeNull();
  });

  it('reveals the image and drops the skeleton once loaded', () => {
    const { container } = render(<LazyImage src="/photo.webp" alt="Photo" />);
    const img = screen.getByRole('img', { name: 'Photo' });

    fireEvent.load(img);

    expect(img.className).toContain('opacity-100');
    expect(container.querySelector('.animate-pulse')).toBeNull();
  });

  it('swaps in the fallback image when the source fails', () => {
    render(
      <LazyImage
        src="/missing.webp"
        alt="Product"
        fallback="https://cdn.example/fallback.webp"
      />
    );

    const img = screen.getByRole('img', { name: 'Product' });
    fireEvent.error(img);

    expect(img).toHaveAttribute('src', 'https://cdn.example/fallback.webp');
  });

  it('derives an aspect ratio from width and height and accepts eager loading', () => {
    const { container } = render(
      <LazyImage src="/photo.webp" alt="Photo" width={400} height={300} loading="eager" />
    );

    const wrapper = container.firstElementChild;
    expect(wrapper.style.aspectRatio).toBe('400 / 300');
    expect(wrapper.style.width).toBe('400px');
    expect(screen.getByRole('img', { name: 'Photo' })).toHaveAttribute('loading', 'eager');
  });
});
