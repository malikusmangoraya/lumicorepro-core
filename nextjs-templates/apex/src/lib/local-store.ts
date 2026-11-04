'use client';

/**
 * localStorage-backed lists with a subscription API, so components can read
 * them through useSyncExternalStore instead of copying them into state inside
 * an effect (which causes a cascading render on every mount).
 *
 * Snapshots are cached: useSyncExternalStore compares by reference and would
 * loop forever if getSnapshot built a new array each call.
 */

export type StoreKey = 'saved' | 'compare' | 'recent';

const STORAGE_KEYS: Record<StoreKey, string> = {
  saved: 'apex:saved',
  compare: 'apex:compare',
  recent: 'apex:recent',
};

const EMPTY: readonly string[] = Object.freeze([]);

const cache: Partial<Record<StoreKey, string[]>> = {};
const listeners = new Set<() => void>();
let loaded = false;

function read(key: StoreKey): string[] {
  try {
    const parsed: unknown = JSON.parse(window.localStorage.getItem(STORAGE_KEYS[key]) ?? '[]');
    return Array.isArray(parsed)
      ? parsed.filter((value): value is string => typeof value === 'string')
      : [];
  } catch {
    return [];
  }
}

function loadOnce() {
  if (loaded || typeof window === 'undefined') return;
  cache.saved = read('saved');
  cache.compare = read('compare');
  cache.recent = read('recent');
  loaded = true;
}

function emit() {
  for (const listener of listeners) listener();
}

export function subscribe(listener: () => void) {
  listeners.add(listener);
  const onStorage = () => {
    loaded = false;
    loadOnce();
    emit();
  };
  window.addEventListener('storage', onStorage);
  return () => {
    listeners.delete(listener);
    window.removeEventListener('storage', onStorage);
  };
}

export function getSnapshot(key: StoreKey): readonly string[] {
  loadOnce();
  return cache[key] ?? EMPTY;
}

export function getServerSnapshot(): readonly string[] {
  return EMPTY;
}

export function setList(key: StoreKey, next: string[]) {
  cache[key] = next;
  loaded = true;
  try {
    window.localStorage.setItem(STORAGE_KEYS[key], JSON.stringify(next));
  } catch {
    // Private mode or a full quota: the list still works for this session.
  }
  emit();
}

export { EMPTY as EMPTY_LIST };
