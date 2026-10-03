/**
 * useCartServerSync — one-way hydration of the server cart into the Zustand cart.
 *
 * CartContext used to do this inside a provider (and pushed local lines back up,
 * which duplicated items server-side on every login). Server state stays in React
 * Query here; the store is only seeded, never mirrored, and a non-empty local cart
 * always wins.
 */
import { useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import cartAPI from '../services/cart';
import { useAuth } from '../context/AuthContext';
import { useCartStore, selectItems } from '../store/cartStore';

/** Map the API cart rows onto the client cart line shape. */
export const mapServerCartItems = (payload) => {
  const rows = payload?.data?.data?.items || payload?.data?.items || [];
  return rows.map((row) => ({
    id: row.product_id ?? row.productId ?? row.id,
    name: row.title || row.product?.title || 'Item',
    price: Number(row.price ?? row.product?.price ?? 0),
    qty: Number(row.quantity ?? row.qty ?? 1),
    image: row.thumbnail || row.product?.thumbnail || '',
    serverId: row.id,
  }));
};

export default function useCartServerSync() {
  const { isAuthenticated } = useAuth();
  const items = useCartStore(selectItems);
  const replaceItems = useCartStore((state) => state.replaceItems);

  const { data } = useQuery({
    queryKey: ['cart'],
    queryFn: () => cartAPI.get(),
    enabled: isAuthenticated,
  });

  const serverItems = useMemo(() => mapServerCartItems(data), [data]);

  useEffect(() => {
    if (!isAuthenticated || serverItems.length === 0) return;
    // A local cart the visitor already built is never overwritten.
    if (items.length > 0) return;
    replaceItems(serverItems);
  }, [isAuthenticated, serverItems, items.length, replaceItems]);
}
