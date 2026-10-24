import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import useReducedMotion from '../../hooks/useReducedMotion';

function stubMatchMedia(matches) {
  const listeners = new Set();
  const mql = {
    matches,
    addEventListener: vi.fn((_event, callback) => listeners.add(callback)),
    removeEventListener: vi.fn((_event, callback) => listeners.delete(callback)),
  };
  vi.stubGlobal('matchMedia', vi.fn((query) => {
    mql.lastQuery = query;
    return mql;
  }));
  return {
    mql,
    emit(value) {
      mql.matches = value;
      listeners.forEach((callback) => callback({ matches: value }));
    },
  };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('useReducedMotion', () => {
  it('queries the reduced-motion media feature and returns its value', () => {
    const media = stubMatchMedia(true);
    const { result } = renderHook(() => useReducedMotion());

    expect(result.current).toBe(true);
    expect(media.mql.lastQuery).toBe('(prefers-reduced-motion: reduce)');
  });

  it('returns false when the user has no preference', () => {
    stubMatchMedia(false);
    const { result } = renderHook(() => useReducedMotion());

    expect(result.current).toBe(false);
  });

  it('reacts to live preference changes', () => {
    const media = stubMatchMedia(false);
    const { result } = renderHook(() => useReducedMotion());

    act(() => media.emit(true));
    expect(result.current).toBe(true);

    act(() => media.emit(false));
    expect(result.current).toBe(false);
  });

  it('unsubscribes from change events on unmount', () => {
    const media = stubMatchMedia(false);
    const { unmount } = renderHook(() => useReducedMotion());

    unmount();

    expect(media.mql.removeEventListener).toHaveBeenCalledWith('change', expect.any(Function));
  });

  it('supports the legacy addListener/removeListener API', () => {
    const listeners = new Set();
    const legacy = {
      matches: false,
      addListener: vi.fn((callback) => listeners.add(callback)),
      removeListener: vi.fn((callback) => listeners.delete(callback)),
    };
    vi.stubGlobal('matchMedia', vi.fn(() => legacy));

    const { result, unmount } = renderHook(() => useReducedMotion());
    expect(result.current).toBe(false);
    expect(legacy.addListener).toHaveBeenCalledTimes(1);

    act(() => listeners.forEach((callback) => callback({ matches: true })));
    expect(result.current).toBe(true);

    unmount();
    expect(legacy.removeListener).toHaveBeenCalledTimes(1);
  });

  it('returns false when matchMedia is unavailable', () => {
    vi.stubGlobal('matchMedia', undefined);
    const { result } = renderHook(() => useReducedMotion());

    expect(result.current).toBe(false);
  });
});
