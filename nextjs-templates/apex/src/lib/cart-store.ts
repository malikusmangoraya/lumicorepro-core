'use client';

/**
 * Cart persistence.
 *
 * Same shape as local-store (a cached snapshot behind useSyncExternalStore) but
 * the value is a list of objects. Prices are kept for display only: the server
 * recomputes every total from the database at checkout, so a tampered
 * localStorage cannot buy a car for a pound.
 */

export type CartItem = {
  kind: 'product' | 'vehicle';
  slug: string;
  title: string;
  price: number;
  currency: string;
  image: string | null;
  quantity: number;
};

const KEY = 'apex:cart';
const EMPTY: readonly CartItem[] = Object.freeze([]);

let cache: CartItem[] | null = null;
const listeners = new Set<() => void>();

function isItem(value: unknown): value is CartItem {
  if (!value || typeof value !== 'object') return false;
  const item = value as Record<string, unknown>;
  return (
    (item.kind === 'product' || item.kind === 'vehicle') &&
    typeof item.slug === 'string' &&
    typeof item.title === 'string' &&
    typeof item.price === 'number' &&
    typeof item.currency === 'string' &&
    typeof item.quantity === 'number' &&
    item.quantity > 0
  );
}

function read(): CartItem[] {
  try {
    const parsed: unknown = JSON.parse(window.localStorage.getItem(KEY) ?? '[]');
    return Array.isArray(parsed) ? parsed.filter(isItem) : [];
  } catch {
    return [];
  }
}

function emit() {
  for (const listener of listeners) listener();
}

export function subscribe(listener: () => void) {
  listeners.add(listener);
  const onStorage = () => {
    cache = null;
    emit();
  };
  window.addEventListener('storage', onStorage);
  return () => {
    listeners.delete(listener);
    window.removeEventListener('storage', onStorage);
  };
}

export function getSnapshot(): readonly CartItem[] {
  if (cache === null) cache = read();
  return cache;
}

export function getServerSnapshot(): readonly CartItem[] {
  return EMPTY;
}

export function setCart(next: CartItem[]) {
  cache = next;
  try {
    window.localStorage.setItem(KEY, JSON.stringify(next));
  } catch {
    // Private mode or quota: the cart still works for this session.
  }
  emit();
}

export function cartCount(items: readonly CartItem[]) {
  return items.reduce((sum, item) => sum + item.quantity, 0);
}

export function cartSubtotal(items: readonly CartItem[]) {
  return Math.round(
    items.reduce((sum, item) => sum + item.price * item.quantity, 0) * 100,
  ) / 100;
}
