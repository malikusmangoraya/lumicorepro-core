import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import useReducedMotion from '../../hooks/useReducedMotion';
import useScrollProgress from '../../hooks/useScrollProgress';

function stubMatchMedia(matches) {
  const listeners = new Set();
  const mql = {
    matches,
    addEventListener: (_event, callback) => listeners.add(callback),
    removeEventListener: (_event, callback) => listeners.delete(callback),
  };
  vi.stubGlobal('matchMedia', vi.fn(() => mql));
  return {
    set(value) {
      mql.matches = value;
      listeners.forEach((callback) => callback({ matches: value }));
    },
  };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('useReducedMotion', () => {
  it('returns false when matchMedia is unavailable', () => {
    vi.stubGlobal('matchMedia', undefined);
    const { result } = renderHook(() => useReducedMotion());
    expect(result.current).toBe(false);
  });

  it('reads the current preference and follows later changes', () => {
    const media = stubMatchMedia(true);
    const { result } = renderHook(() => useReducedMotion());
    expect(result.current).toBe(true);

    act(() => media.set(false));
    expect(result.current).toBe(false);

    act(() => media.set(true));
    expect(result.current).toBe(true);
  });
});

describe('useScrollProgress', () => {
  function stubPage({ scrollable, scrollY }) {
    Object.defineProperty(document.documentElement, 'scrollHeight', {
      value: scrollable,
      configurable: true,
    });
    Object.defineProperty(document.documentElement, 'clientHeight', {
      value: scrollable / 2,
      configurable: true,
    });
    Object.defineProperty(window, 'scrollY', {
      value: scrollY,
      configurable: true,
      writable: true,
    });
  }

  const nextFrame = () => act(() => new Promise((resolve) => setTimeout(resolve, 60)));

  it('starts at 0', () => {
    stubPage({ scrollable: 2000, scrollY: 0 });
    const { result } = renderHook(() => useScrollProgress());
    expect(result.current).toBe(0);
  });

  it('reports the scrolled fraction after a scroll event', async () => {
    stubPage({ scrollable: 2000, scrollY: 500 });
    const { result } = renderHook(() => useScrollProgress());

    act(() => {
      window.dispatchEvent(new Event('scroll'));
    });
    await nextFrame();

    // (500 - 0) / (2000 - 1000) = 0.5 — scrollable = scrollHeight - clientHeight
    expect(result.current).toBeCloseTo(0.5, 5);
  });

  it('returns 0 for a page that cannot scroll', () => {
    stubPage({ scrollable: 800, scrollY: 0 });
    const { result } = renderHook(() => useScrollProgress());
    expect(result.current).toBe(0);
  });
});
