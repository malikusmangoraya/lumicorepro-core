import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import useWindowSize from '../../hooks/useWindowSize';

function setViewport(width, height = 800) {
  Object.defineProperty(window, 'innerWidth', { configurable: true, writable: true, value: width });
  Object.defineProperty(window, 'innerHeight', { configurable: true, writable: true, value: height });
}

beforeEach(() => {
  setViewport(1024, 768);
});

afterEach(() => {
  setViewport(1024, 768);
});

describe('useWindowSize', () => {
  it('reports the current viewport width and height', () => {
    setViewport(1280, 720);
    const { result } = renderHook(() => useWindowSize());

    expect(result.current.width).toBe(1280);
    expect(result.current.height).toBe(720);
  });

  it('classifies mobile, tablet and desktop breakpoints', () => {
    setViewport(375, 812);
    const mobile = renderHook(() => useWindowSize()).result.current;
    expect(mobile).toMatchObject({ isMobile: true, isTablet: false, isDesktop: false });

    setViewport(768, 1024);
    const tablet = renderHook(() => useWindowSize()).result.current;
    expect(tablet).toMatchObject({ isMobile: false, isTablet: true, isDesktop: false });

    setViewport(1440, 900);
    const desktop = renderHook(() => useWindowSize()).result.current;
    expect(desktop).toMatchObject({ isMobile: false, isTablet: false, isDesktop: true });
  });

  it('uses the 640/1024 boundaries consistently', () => {
    setViewport(639);
    expect(renderHook(() => useWindowSize()).result.current.isMobile).toBe(true);

    setViewport(640);
    expect(renderHook(() => useWindowSize()).result.current.isTablet).toBe(true);

    setViewport(1023);
    expect(renderHook(() => useWindowSize()).result.current.isDesktop).toBe(false);

    setViewport(1024);
    expect(renderHook(() => useWindowSize()).result.current.isDesktop).toBe(true);
  });

  it('updates after a resize event', () => {
    setViewport(500, 800);
    const { result } = renderHook(() => useWindowSize());
    expect(result.current.isMobile).toBe(true);

    setViewport(1200, 900);
    act(() => {
      window.dispatchEvent(new Event('resize'));
    });

    expect(result.current).toMatchObject({
      width: 1200,
      height: 900,
      isMobile: false,
      isTablet: false,
      isDesktop: true,
    });
  });

  it('removes its resize listener on unmount', () => {
    const removeSpy = vi.spyOn(window, 'removeEventListener');
    const addSpy = vi.spyOn(window, 'addEventListener');

    const { unmount } = renderHook(() => useWindowSize());
    expect(addSpy).toHaveBeenCalledWith('resize', expect.any(Function));

    unmount();
    expect(removeSpy).toHaveBeenCalledWith('resize', expect.any(Function));

    addSpy.mockRestore();
    removeSpy.mockRestore();
  });
});
