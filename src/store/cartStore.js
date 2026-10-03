/**
 * cartStore — Zustand store for the client cart (AGENTS.md §8: cart → Zustand).
 *
 * Replaces `context/CartContext.jsx`. Only client cart lines live here; anything
 * fetched from the backend stays in React Query (see `hooks/useCartServerSync`).
 *
 * Selectors deliberately return either a reference-stable slice (`items`) or a
 * primitive (count/subtotal). Zustand v5 compares snapshots with `Object.is`, so
 * a selector that builds a fresh object on every call would re-render forever —
 * use `useCartTotals()` for the derived object instead.
 */
import { useMemo } from 'react';
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/** localStorage key — unchanged from CartContext so existing carts survive. */
export const CART_STORAGE_KEY = 'lumicore_cart';

/** Flat demo shipping rate, shared by the cart and checkout pages. */
export const SHIPPING_FLAT_RATE = 8;

const normaliseQty = (qty) => {
  const n = Math.floor(Number(qty));
  return Number.isFinite(n) && n > 0 ? n : 1;
};

const toLine = (product, quantity) => ({
  id: product.id,
  name: product.name,
  price: Number(product.price) || 0,
  qty: normaliseQty(quantity),
  image: product.image || '',
  serverId: product.serverId,
});

/**
 * Persist storage that also upgrades the legacy CartContext payload.
 * CartContext wrote a bare JSON array; the persist middleware expects a
 * `{ state, version }` envelope, so an array found under the same key is wrapped.
 */
const cartStorage = {
  getItem: (name) => {
    try {
      const raw = localStorage.getItem(name);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? { state: { items: parsed }, version: 0 } : parsed;
    } catch {
      return null;
    }
  },
  setItem: (name, value) => {
    try {
      localStorage.setItem(name, JSON.stringify(value));
    } catch {
      /* quota exceeded / storage disabled — cart stays in memory */
    }
  },
  removeItem: (name) => {
    try {
      localStorage.removeItem(name);
    } catch {
      /* storage disabled */
    }
  },
};

export const useCartStore = create(
  persist(
    (set) => ({
      items: [],

      /** Add `quantity` of `product`; an existing line is incremented. */
      addItem: (product, quantity = 1) =>
        set((state) => {
          const existing = state.items.find((i) => i.id === product.id);
          if (existing) {
            return {
              items: state.items.map((i) =>
                i.id === product.id ? { ...i, qty: i.qty + normaliseQty(quantity) } : i
              ),
            };
          }
          return { items: [...state.items, toLine(product, quantity)] };
        }),

      removeItem: (id) => set((state) => ({ items: state.items.filter((i) => i.id !== id) })),

      /** Set an absolute quantity; values below 1 clamp to 1. */
      updateQty: (id, qty) =>
        set((state) => ({
          items: state.items.map((i) => (i.id === id ? { ...i, qty: normaliseQty(qty) } : i)),
        })),

      clear: () => set({ items: [] }),

      /** Replace every line — used when hydrating from the server cart. */
      replaceItems: (items) => set({ items: (items || []).map((i) => toLine(i, i.qty)) }),
    }),
    {
      name: CART_STORAGE_KEY,
      storage: cartStorage,
      partialize: (state) => ({ items: state.items }),
    }
  )
);

/* ── Selectors (`state => state.property` pattern) ───────────────────────── */
export const selectItems = (state) => state.items;
export const selectCount = (state) => state.items.reduce((sum, i) => sum + i.qty, 0);
export const selectSubtotal = (state) =>
  state.items.reduce((sum, i) => sum + i.price * i.qty, 0);

/** Pure totals helper — shipping is only charged when the cart has lines. */
export const computeTotals = (items = []) => {
  const count = items.reduce((sum, i) => sum + i.qty, 0);
  const subtotal = items.reduce((sum, i) => sum + i.price * i.qty, 0);
  const shipping = items.length > 0 ? SHIPPING_FLAT_RATE : 0;
  return { count, subtotal, shipping, total: subtotal + shipping };
};

/** Derived totals object, memoised on `items` so no selector builds a new object. */
export function useCartTotals() {
  const items = useCartStore(selectItems);
  return useMemo(() => computeTotals(items), [items]);
}

/**
 * Drop-in replacement for the removed `useCart()` context hook.
 * Same shape: { items, count, subtotal, addItem, removeItem, updateQty, clear }.
 */
export function useCart() {
  const items = useCartStore(selectItems);
  const addItem = useCartStore((state) => state.addItem);
  const removeItem = useCartStore((state) => state.removeItem);
  const updateQty = useCartStore((state) => state.updateQty);
  const clear = useCartStore((state) => state.clear);
  const count = useCartStore(selectCount);
  const subtotal = useCartStore(selectSubtotal);

  return useMemo(
    () => ({ items, count, subtotal, addItem, removeItem, updateQty, clear }),
    [items, count, subtotal, addItem, removeItem, updateQty, clear]
  );
}

export default useCartStore;
