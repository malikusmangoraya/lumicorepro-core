import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import useDebounce from '../../hooks/useDebounce';

describe('useDebounce', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('updates the value after the delay and resets the timer on changes', () => {
    vi.useFakeTimers();
    const { result, rerender } = renderHook(({ value }) => useDebounce(value, 300), {
      initialProps: { value: 'first' },
    });

    expect(result.current).toBe('first');

    rerender({ value: 'second' });
    act(() => vi.advanceTimersByTime(200));
    rerender({ value: 'third' });
    act(() => vi.advanceTimersByTime(299));
    expect(result.current).toBe('first');

    act(() => vi.advanceTimersByTime(1));
    expect(result.current).toBe('third');
  });
});
