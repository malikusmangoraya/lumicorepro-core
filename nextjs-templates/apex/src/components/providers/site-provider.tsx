'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  useSyncExternalStore,
} from 'react';
import { CheckCircle2, X } from 'lucide-react';
import {
  getServerSnapshot,
  getSnapshot,
  getString,
  setList,
  setString,
  subscribe,
  type StoreKey,
} from '@/lib/local-store';
import {
  isLocale,
  LOCALE_META,
  translate,
  type Locale,
  type MessageKey,
} from '@/lib/i18n/dictionaries';
import {
  cartCount,
  cartSubtotal,
  getServerSnapshot as getCartServerSnapshot,
  getSnapshot as getCartSnapshot,
  setCart,
  subscribe as subscribeCart,
  type CartItem,
} from '@/lib/cart-store';

const LIMITS = { saved: 60, compare: 3, recent: 6 } as const;

type Toast = { id: number; message: string };

type SiteContextValue = {
  saved: readonly string[];
  compare: readonly string[];
  recent: readonly string[];
  hydrated: boolean;
  isSaved: (slug: string) => boolean;
  toggleSaved: (slug: string) => void;
  isCompared: (slug: string) => boolean;
  /** Returns false when the compare tray is already full. */
  toggleCompare: (slug: string) => boolean;
  clearCompare: () => void;
  addRecent: (slug: string) => void;
  notify: (message: string) => void;
  cart: readonly CartItem[];
  cartCount: number;
  cartSubtotal: number;
  addToCart: (item: Omit<CartItem, 'quantity'>, quantity?: number) => void;
  setQuantity: (slug: string, quantity: number) => void;
  removeFromCart: (slug: string) => void;
  clearCart: () => void;
  locale: Locale;
  setLocale: (locale: Locale) => void;
  theme: 'dark' | 'light';
  setTheme: (theme: 'dark' | 'light') => void;
  t: (key: MessageKey) => string;
};

const SiteContext = createContext<SiteContextValue | null>(null);

const useList = (key: StoreKey) =>
  useSyncExternalStore(subscribe, () => getSnapshot(key), getServerSnapshot);

/** true after hydration, false during SSR — keeps the first paint identical. */
const useHydrated = () => useSyncExternalStore(subscribe, () => true, () => false);

export function SiteProvider({ children }: { children: React.ReactNode }) {
  const saved = useList('saved');
  const compare = useList('compare');
  const recent = useList('recent');
  const hydrated = useHydrated();
  const cart = useSyncExternalStore(subscribeCart, getCartSnapshot, getCartServerSnapshot);

  const storedLocale = useSyncExternalStore(
    subscribe,
    () => getString('apex:locale') ?? 'en',
    () => 'en',
  );
  const locale: Locale = isLocale(storedLocale) ? storedLocale : 'en';
  const theme = useSyncExternalStore(
    subscribe,
    () => getString('apex:theme') ?? 'dark',
    () => 'dark',
  ) as 'dark' | 'light';

  // Both of these only touch the document, never React state.
  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = LOCALE_META[locale].dir;
  }, [locale]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
  }, [theme]);

  const setLocale = useCallback((next: Locale) => setString('apex:locale', next), []);
  const setTheme = useCallback(
    (next: 'dark' | 'light') => setString('apex:theme', next),
    [],
  );
  const t = useCallback((key: MessageKey) => translate(locale, key), [locale]);

  const [toasts, setToasts] = useState<Toast[]>([]);

  const notify = useCallback((message: string) => {
    const id = Date.now() + Math.random();
    setToasts((current) => [...current, { id, message }]);
    window.setTimeout(() => {
      setToasts((current) => current.filter((toast) => toast.id !== id));
    }, 3500);
  }, []);

  const toggleSaved = useCallback(
    (slug: string) => {
      const current = saved;
      const next = current.includes(slug)
        ? current.filter((item) => item !== slug)
        : [slug, ...current].slice(0, LIMITS.saved);
      setList('saved', next);
    },
    [saved],
  );

  const toggleCompare = useCallback(
    (slug: string) => {
      const current = compare;
      if (current.includes(slug)) {
        setList('compare', current.filter((item) => item !== slug));
        return true;
      }
      if (current.length >= LIMITS.compare) return false;
      setList('compare', [...current, slug]);
      return true;
    },
    [compare],
  );

  const clearCompare = useCallback(() => setList('compare', []), []);

  const addRecent = useCallback(
    (slug: string) => {
      const current = recent;
      if (current[0] === slug) return;
      setList('recent', [slug, ...current.filter((item) => item !== slug)].slice(0, LIMITS.recent));
    },
    [recent],
  );

  const addToCart = useCallback(
    (item: Omit<CartItem, 'quantity'>, quantity = 1) => {
      const current = cart;
      const existing = current.find((entry) => entry.slug === item.slug);
      const next = existing
        ? current.map((entry) =>
            entry.slug === item.slug
              ? { ...entry, quantity: Math.min(99, entry.quantity + quantity) }
              : entry,
          )
        : [...current, { ...item, quantity: Math.min(99, Math.max(1, quantity)) }];
      setCart(next);
    },
    [cart],
  );

  const setQuantity = useCallback(
    (slug: string, quantity: number) => {
      if (quantity < 1) {
        setCart(cart.filter((entry) => entry.slug !== slug));
        return;
      }
      setCart(
        cart.map((entry) =>
          entry.slug === slug ? { ...entry, quantity: Math.min(99, quantity) } : entry,
        ),
      );
    },
    [cart],
  );

  const removeFromCart = useCallback(
    (slug: string) => setCart(cart.filter((entry) => entry.slug !== slug)),
    [cart],
  );

  const clearCart = useCallback(() => setCart([]), []);

  const value = useMemo<SiteContextValue>(
    () => ({
      saved,
      compare,
      recent,
      hydrated,
      isSaved: (slug) => saved.includes(slug),
      toggleSaved,
      isCompared: (slug) => compare.includes(slug),
      toggleCompare,
      clearCompare,
      addRecent,
      notify,
      cart,
      cartCount: cartCount(cart),
      cartSubtotal: cartSubtotal(cart),
      addToCart,
      setQuantity,
      removeFromCart,
      clearCart,
      locale,
      setLocale,
      theme,
      setTheme,
      t,
    }),
    [
      locale,
      setLocale,
      theme,
      setTheme,
      t,
      saved,
      compare,
      recent,
      hydrated,
      toggleSaved,
      toggleCompare,
      clearCompare,
      addRecent,
      notify,
      cart,
      addToCart,
      setQuantity,
      removeFromCart,
      clearCart,
    ],
  );

  return (
    <SiteContext.Provider value={value}>
      {children}
      <ToastRegion
        toasts={toasts}
        onDismiss={(id) => setToasts((current) => current.filter((toast) => toast.id !== id))}
      />
    </SiteContext.Provider>
  );
}

function ToastRegion({ toasts, onDismiss }: { toasts: Toast[]; onDismiss: (id: number) => void }) {
  return (
    <div
      aria-live="polite"
      aria-atomic="false"
      className="pointer-events-none fixed inset-x-0 bottom-5 z-[100] flex flex-col items-center gap-2 px-4"
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className="pointer-events-auto flex w-full max-w-sm items-start gap-2.5 rounded-panel border border-line bg-surface px-4 py-3 shadow-[0_18px_50px_-20px_rgb(0_0_0/0.8)]"
        >
          <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-accent" aria-hidden="true" />
          <p className="flex-1 text-sm text-heading">{toast.message}</p>
          <button
            type="button"
            onClick={() => onDismiss(toast.id)}
            aria-label="Dismiss notification"
            className="rounded p-0.5 text-muted transition-colors hover:text-heading"
          >
            <X className="size-3.5" aria-hidden="true" />
          </button>
        </div>
      ))}
    </div>
  );
}

export function useSite() {
  const context = useContext(SiteContext);
  if (!context) throw new Error('useSite must be used inside <SiteProvider>');
  return context;
}

export { LIMITS as SITE_LIMITS };
