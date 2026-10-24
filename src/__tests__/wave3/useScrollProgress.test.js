import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import useScrollProgress from '../../hooks/useScrollProgress';

function stubPage({ scrollHeight = 2000, clientHeight = 1000, scrollY = 0 }) {
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

const flushFrame = () => act(() => new Promise((resolve) => setTimeout(resolve, 50)));

afterEach(() => {
  vi.restoreAllMocks();
});

describe('useScrollProgress', () => {
  it('clamps the reported progress to 1 past the bottom of the page', async () => {
    stubPage({ scrollHeight: 1200, clientHeight: 400, scrollY: 5000 });
    const { result } = renderHook(() => useScrollProgress());

    act(() => {
      window.dispatchEvent(new Event('scroll'));
    });
    await flushFrame();

    expect(result.current).toBe(1);
  });

  it('never reports a negative fraction when scrollY is negative', async () => {
    stubPage({ scrollHeight: 1200, clientHeight: 400, scrollY: -300 });
    const { result } = renderHook(() => useScrollProgress());

    act(() => {
      window.dispatchEvent(new Event('scroll'));
    });
    await flushFrame();

    expect(result.current).toBe(0);
  });

  it('recomputes on resize as well as scroll', async () => {
    stubPage({ scrollHeight: 2000, clientHeight: 1000, scrollY: 0 });
    const { result } = renderHook(() => useScrollProgress());
    expect(result.current).toBe(0);

    Object.defineProperty(window, 'scrollY', { value: 250, configurable: true, writable: true });
    act(() => {
      window.dispatchEvent(new Event('resize'));
    });
    await flushFrame();

    expect(result.current).toBeCloseTo(0.25, 5);
  });

  it('removes both passive listeners on unmount', () => {
    stubPage({ scrollHeight: 2000, clientHeight: 1000, scrollY: 0 });
    const removeSpy = vi.spyOn(window, 'removeEventListener');
    const { unmount } = renderHook(() => useScrollProgress());

    unmount();

    expect(removeSpy.mock.calls.map(([event]) => event)).toEqual(
      expect.arrayContaining(['scroll', 'resize'])
    );
  });
});
