import { describe, it, expect, beforeEach } from 'vitest';
import useCartStore, {
  CART_STORAGE_KEY,
  SHIPPING_FLAT_RATE,
  computeTotals,
  selectCount,
  selectSubtotal,
  selectItems,
} from '../../store/cartStore';

/**
 * Cart is the highest-risk client state for revenue: wrong quantities or totals
 * become wrong charges. Zustand store is module-level, so reset state + storage
 * between tests.
 */
const product = (id, price = 10, name = `Product ${id}`) => ({ id, name, price });

beforeEach(() => {
  localStorage.clear();
  useCartStore.setState({ items: [] });
});

describe('cartStore actions', () => {
  it('adds a new line with normalised quantity', () => {
    useCartStore.getState().addItem(product(1, 25), 2);
    const { items } = useCartStore.getState();
    expect(items).toHaveLength(1);
    expect(items[0]).toMatchObject({ id: 1, price: 25, qty: 2 });
  });

  it('clamps invalid quantities to 1 on add', () => {
    useCartStore.getState().addItem(product(1), 0);
    useCartStore.getState().addItem(product(2), -3);
    useCartStore.getState().addItem(product(3), 'nope');
    const qtys = useCartStore.getState().items.map((i) => i.qty);
    expect(qtys).toEqual([1, 1, 1]);
  });

  it('increments quantity when the same product is added again', () => {
    useCartStore.getState().addItem(product(1), 1);
    useCartStore.getState().addItem(product(1), 3);
    expect(useCartStore.getState().items).toHaveLength(1);
    expect(useCartStore.getState().items[0].qty).toBe(4);
  });

  it('updates an absolute quantity and clamps below 1', () => {
    useCartStore.getState().addItem(product(1), 2);
    useCartStore.getState().updateQty(1, 5);
    expect(useCartStore.getState().items[0].qty).toBe(5);
    useCartStore.getState().updateQty(1, 0);
    expect(useCartStore.getState().items[0].qty).toBe(1);
  });

  it('removes a line and clears the whole cart', () => {
    const s = useCartStore.getState();
    s.addItem(product(1));
    s.addItem(product(2));
    s.removeItem(1);
    expect(useCartStore.getState().items.map((i) => i.id)).toEqual([2]);
    s.clear();
    expect(useCartStore.getState().items).toEqual([]);
  });

  it('replaceItems hydrates from server shape', () => {
    useCartStore.getState().replaceItems([
      { id: 9, name: 'Server item', price: '12.50', qty: 2, serverId: 'srv-9' },
    ]);
    const [line] = useCartStore.getState().items;
    expect(line).toMatchObject({ id: 9, price: 12.5, qty: 2, serverId: 'srv-9' });
  });
});

describe('selectors and totals', () => {
  it('selectCount and selectSubtotal aggregate lines', () => {
    useCartStore.getState().addItem(product(1, 10), 2);
    useCartStore.getState().addItem(product(2, 5.5), 1);
    const state = useCartStore.getState();
    expect(selectCount(state)).toBe(3);
    expect(selectSubtotal(state)).toBe(25.5);
    expect(selectItems(state)).toHaveLength(2);
  });

  it('computeTotals adds flat shipping only for non-empty carts', () => {
    expect(computeTotals([])).toEqual({ count: 0, subtotal: 0, shipping: 0, total: 0 });
    const totals = computeTotals([
      { price: 10, qty: 2 },
      { price: 5, qty: 1 },
    ]);
    expect(totals).toEqual({
      count: 3,
      subtotal: 25,
      shipping: SHIPPING_FLAT_RATE,
      total: 25 + SHIPPING_FLAT_RATE,
    });
  });
});

describe('persistence', () => {
  it('persists items under the canonical storage key', () => {
    useCartStore.getState().addItem(product(1), 1);
    const raw = localStorage.getItem(CART_STORAGE_KEY);
    expect(raw).toBeTruthy();
    expect(JSON.parse(raw).state.items).toHaveLength(1);
  });
});
