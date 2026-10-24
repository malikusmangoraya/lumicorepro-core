import { renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const auth = vi.hoisted(() => ({ isAuthenticated: true }));
const cartGet = vi.hoisted(() => vi.fn());
const query = vi.hoisted(() => ({ options: null, result: { data: undefined } }));

vi.mock('../../context/AuthContext', () => ({
  useAuth: () => ({ isAuthenticated: auth.isAuthenticated }),
}));

vi.mock('../../services/cart', () => ({
  default: { get: cartGet },
}));

vi.mock('@tanstack/react-query', () => ({
  useQuery: (options) => {
    query.options = options;
    return query.result;
  },
}));

import useCartServerSync, { mapServerCartItems } from '../../hooks/useCartServerSync';
import { useCartStore } from '../../store/cartStore';

const serverRow = {
  id: 55,
  product_id: 9,
  title: 'Aurora Headphones',
  price: '149.50',
  quantity: '2',
  thumbnail: 'https://cdn.test/aurora.webp',
};

beforeEach(() => {
  localStorage.clear();
  auth.isAuthenticated = true;
  cartGet.mockReset();
  query.options = null;
  query.result = { data: undefined };
  useCartStore.setState({ items: [] });
});

afterEach(() => {
  vi.clearAllMocks();
});

describe('mapServerCartItems', () => {
  it('maps the nested API envelope onto client cart lines', () => {
    const mapped = mapServerCartItems({ data: { data: { items: [serverRow] } } });

    expect(mapped).toEqual([
      {
        id: 9,
        name: 'Aurora Headphones',
        price: 149.5,
        qty: 2,
        image: 'https://cdn.test/aurora.webp',
        serverId: 55,
      },
    ]);
  });

  it('accepts the flat envelope and fills defaults for missing fields', () => {
    const mapped = mapServerCartItems({ data: { items: [{ id: 3, productId: 4, qty: 5 }] } });

    expect(mapped).toEqual([
      { id: 4, name: 'Item', price: 0, qty: 5, image: '', serverId: 3 },
    ]);
    expect(mapServerCartItems(undefined)).toEqual([]);
  });
});

describe('useCartServerSync', () => {
  it('does not fetch the server cart for anonymous visitors', () => {
    auth.isAuthenticated = false;

    renderHook(() => useCartServerSync());

    expect(query.options).toMatchObject({ queryKey: ['cart'], enabled: false });
    expect(useCartStore.getState().items).toEqual([]);
  });

  it('seeds an empty local cart from the server', async () => {
    query.result = { data: { data: { data: { items: [serverRow] } } } };

    renderHook(() => useCartServerSync());

    expect(query.options.enabled).toBe(true);
    await waitFor(() => expect(useCartStore.getState().items).toHaveLength(1));
    expect(useCartStore.getState().items[0]).toMatchObject({
      id: 9,
      name: 'Aurora Headphones',
      qty: 2,
      serverId: 55,
    });
  });

  it('never overwrites a cart the visitor already built locally', async () => {
    useCartStore.setState({
      items: [{ id: 1, name: 'Local item', price: 5, qty: 1, image: '', serverId: undefined }],
    });
    query.result = { data: { data: { data: { items: [serverRow] } } } };

    renderHook(() => useCartServerSync());
    await new Promise((resolve) => setTimeout(resolve, 20));

    expect(useCartStore.getState().items).toHaveLength(1);
    expect(useCartStore.getState().items[0].name).toBe('Local item');
  });

  it('leaves the store alone when the server cart is empty', async () => {
    query.result = { data: { data: { data: { items: [] } } } };

    renderHook(() => useCartServerSync());
    await new Promise((resolve) => setTimeout(resolve, 20));

    expect(useCartStore.getState().items).toEqual([]);
  });
});
