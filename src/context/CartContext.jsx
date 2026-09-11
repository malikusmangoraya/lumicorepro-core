import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import cartAPI from '../services/cart';

const CartContext = createContext(null);
const STORAGE_KEY = 'lumicore_cart';

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error('useCart must be used within CartProvider');
  return ctx;
}

export function CartProvider({ children }) {
  const [items, setItems] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
    } catch {
      return [];
    }
  });
  const [serverSynced, setServerSynced] = useState(false);

  const isAuthed = !!localStorage.getItem('auth_token');

  // On login: load server cart and merge with localStorage cart
  useEffect(() => {
    if (!isAuthed || serverSynced) return;
    (async () => {
      try {
        const { data } = await cartAPI.get();
        const serverItems = data?.data?.items || [];
        if (serverItems.length > 0) {
          setItems((prev) => {
            const merged = [...prev];
            for (const si of serverItems) {
              const idx = merged.findIndex((m) => m.id === si.product_id);
              if (idx >= 0) {
                merged[idx] = { ...merged[idx], qty: merged[idx].qty + si.quantity, serverId: si.id };
              } else {
                merged.push({
                  id: si.product_id,
                  name: si.title || si.product?.title || 'Item',
                  price: parseFloat(si.price),
                  qty: si.quantity,
                  image: si.thumbnail || si.product?.thumbnail || '',
                  serverId: si.id,
                });
              }
            }
            return merged;
          });
        } else {
          // Server cart is empty — push local cart to server
          for (const item of items) {
            await cartAPI.addItem(item.id, item.qty).catch(() => {});
          }
        }
        setServerSynced(true);
      } catch {
        // Not logged in or server unreachable — continue with localStorage
        setServerSynced(true);
      }
    })();
  }, [isAuthed, serverSynced]);

  // Persist to localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  }, [items]);

  const addItem = useCallback(
    async (product, quantity = 1) => {
      setItems((prev) => {
        const existing = prev.find((i) => i.id === product.id);
        if (existing) {
          return prev.map((i) => (i.id === product.id ? { ...i, qty: i.qty + quantity } : i));
        }
        return [
          ...prev,
          {
            id: product.id,
            name: product.name,
            price: product.price,
            qty: quantity,
            image: product.image,
          },
        ];
      });
      if (isAuthed) {
        await cartAPI.addItem(product.id, quantity).catch(() => {});
      }
    },
    [isAuthed]
  );

  const removeItem = useCallback(
    async (id) => {
      setItems((prev) => prev.filter((i) => i.id !== id));
      if (isAuthed) {
        const item = items.find((i) => i.id === id);
        if (item?.serverId) {
          await cartAPI.removeItem(item.serverId).catch(() => {});
        }
      }
    },
    [isAuthed, items]
  );

  const updateQty = useCallback(
    async (id, qty) => {
      const newQty = Math.max(1, qty);
      setItems((prev) => prev.map((i) => (i.id === id ? { ...i, qty: newQty } : i)));
      if (isAuthed) {
        const item = items.find((i) => i.id === id);
        if (item?.serverId) {
          await cartAPI.updateItem(item.serverId, newQty).catch(() => {});
        }
      }
    },
    [isAuthed, items]
  );

  const clear = useCallback(async () => {
    setItems([]);
    if (isAuthed) {
      await cartAPI.clear().catch(() => {});
    }
  }, [isAuthed]);

  const subtotal = useMemo(() => items.reduce((sum, i) => sum + i.price * i.qty, 0), [items]);
  const count = useMemo(() => items.reduce((sum, i) => sum + i.qty, 0), [items]);

  const value = useMemo(
    () => ({
      items,
      count,
      subtotal,
      addItem,
      removeItem,
      updateQty,
      clear,
    }),
    [items, count, subtotal, addItem, removeItem, updateQty, clear]
  );

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export default CartContext;
