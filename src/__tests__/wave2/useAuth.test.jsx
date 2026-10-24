import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AppContext } from '../../context/AppContext';
import { AuthProvider } from '../../context/AuthContext';
import { useAuth, useCart } from '../../hooks/useAuth';
import useCartStore from '../../store/cartStore';

const authUser = { id: 3, name: 'Grace Hopper', role: 'admin' };

function appValue(overrides = {}) {
  return {
    user: authUser,
    token: 'jwt-3',
    isAuthenticated: true,
    login: vi.fn(),
    logout: vi.fn(),
    ...overrides,
  };
}

function wrapperWith(app) {
  return ({ children }) => (
    <AppContext.Provider value={app}>
      <AuthProvider>{children}</AuthProvider>
    </AppContext.Provider>
  );
}

beforeEach(() => {
  localStorage.clear();
  useCartStore.setState({ items: [] });
  vi.clearAllMocks();
});

describe('useAuth re-export', () => {
  it('throws outside AuthProvider', () => {
    expect(() => renderHook(() => useAuth())).toThrow('useAuth must be used within AuthProvider');
  });

  it('exposes the authenticated user from the app context', () => {
    const { result } = renderHook(() => useAuth(), { wrapper: wrapperWith(appValue()) });

    expect(result.current.user).toEqual(authUser);
    expect(result.current.token).toBe('jwt-3');
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(typeof result.current.login).toBe('function');
    expect(typeof result.current.logout).toBe('function');
  });

  it('reflects a signed-out app context', () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: wrapperWith(appValue({ user: null, token: null, isAuthenticated: false })),
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });
});

describe('useCart re-export', () => {
  it('exposes cart items, count and subtotal from the store', () => {
    const { result } = renderHook(() => useCart());

    expect(result.current.items).toEqual([]);
    expect(result.current.count).toBe(0);
    expect(result.current.subtotal).toBe(0);
  });

  it('tracks store updates through the hook', () => {
    const { result } = renderHook(() => useCart());

    act(() => {
      result.current.addItem({ id: 1, name: 'Widget', price: 12.5 }, 2);
    });

    expect(result.current.items).toHaveLength(1);
    expect(result.current.count).toBe(2);
    expect(result.current.subtotal).toBe(25);
  });

  it('updates quantity and clears the cart through the hook actions', () => {
    const { result } = renderHook(() => useCart());

    act(() => result.current.addItem({ id: 7, name: 'Gadget', price: 5 }, 1));
    act(() => result.current.updateQty(7, 3));
    expect(result.current.count).toBe(3);
    expect(result.current.subtotal).toBe(15);

    act(() => result.current.removeItem(7));
    expect(result.current.items).toEqual([]);
    expect(result.current.count).toBe(0);
  });
});
