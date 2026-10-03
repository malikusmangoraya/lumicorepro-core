import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import useLocalStorage from '../../hooks/useLocalStorage';

describe('useLocalStorage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('initializes from storage and persists direct and functional updates', () => {
    localStorage.setItem('preferences', JSON.stringify({ count: 2 }));
    const { result } = renderHook(() => useLocalStorage('preferences', { count: 0 }));

    expect(result.current[0]).toEqual({ count: 2 });

    act(() => result.current[1]((current) => ({ count: current.count + 1 })));

    expect(result.current[0]).toEqual({ count: 3 });
    expect(JSON.parse(localStorage.getItem('preferences'))).toEqual({ count: 3 });
  });

  it('uses the initial value when no value is stored and restores it after removal', () => {
    const { result } = renderHook(() => useLocalStorage('theme', 'dark'));

    act(() => result.current[1]('light'));
    expect(result.current[0]).toBe('light');

    act(() => result.current[2]());
    expect(result.current[0]).toBe('dark');
    expect(localStorage.getItem('theme')).toBeNull();
  });

  it('synchronizes changes from another tab', () => {
    const { result } = renderHook(() => useLocalStorage('language', 'en'));
    localStorage.setItem('language', JSON.stringify('ur'));

    act(() => {
      window.dispatchEvent(
        new StorageEvent('storage', {
          key: 'language',
          newValue: JSON.stringify('ur'),
          storageArea: localStorage,
        })
      );
    });

    expect(result.current[0]).toBe('ur');
  });
});
