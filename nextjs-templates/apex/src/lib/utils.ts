import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const currencyFormatters = new Map<string, Intl.NumberFormat>();

/** Format a listing price in its own currency — never converts. */
export function formatCurrency(amount: number, currency = 'USD', locale = 'en-US') {
  const key = `${locale}:${currency}`;
  let formatter = currencyFormatters.get(key);
  if (!formatter) {
    formatter = new Intl.NumberFormat(locale, {
      style: 'currency',
      currency,
      maximumFractionDigits: 0,
    });
    currencyFormatters.set(key, formatter);
  }
  return formatter.format(amount);
}

export function formatMileage(mileage: number, unit: string) {
  return `${new Intl.NumberFormat('en-US').format(mileage)} ${unit}`;
}

export function formatDate(value: Date | string, locale = 'en-US') {
  const date = typeof value === 'string' ? new Date(value) : value;
  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(date);
}

export function slugify(input: string) {
  return input
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-');
}

/** JSON columns are stored as text on SQLite; these keep call sites typed. */
export function parseJson<T>(value: string | null | undefined, fallback: T): T {
  if (!value) return fallback;
  try {
    return JSON.parse(value) as T;
  } catch {
    return fallback;
  }
}

export function orderNumber(seq: number) {
  return `APX-${new Date().getFullYear()}-${String(seq).padStart(5, '0')}`;
}
