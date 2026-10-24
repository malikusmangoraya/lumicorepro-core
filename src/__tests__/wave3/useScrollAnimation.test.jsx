import { renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

const inView = vi.hoisted(() => ({ value: true, ref: null, options: null }));

vi.mock('framer-motion', () => ({
  useInView: (ref, options) => {
    inView.ref = ref;
    inView.options = options;
    return inView.value;
  },
}));

import useScrollAnimation from '../../hooks/useScrollAnimation';

describe('useScrollAnimation', () => {
  it('returns a ref and forwards the documented default options to useInView', () => {
    const { result } = renderHook(() => useScrollAnimation());

    expect(result.current.inView).toBe(true);
    expect(result.current.ref).toEqual({ current: null });
    expect(inView.ref).toBe(result.current.ref);
    expect(inView.options).toEqual({ margin: '-40px', once: true, amount: 0.1 });
  });

  it('honours caller overrides and reflects an out-of-view result', () => {
    inView.value = false;

    const { result } = renderHook(() =>
      useScrollAnimation({ margin: '0px', once: false, amount: 0.5 })
    );

    expect(result.current.inView).toBe(false);
    expect(inView.options).toEqual({ margin: '0px', once: false, amount: 0.5 });
  });
});
