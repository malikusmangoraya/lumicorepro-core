import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import helpers, {
  calculatePercentage,
  capitalize,
  chunkArray,
  clearStorage,
  cn,
  copyToClipboard,
  debounce,
  formatCurrency,
  formatDate,
  formatDateISO,
  formatDateTime,
  formatNumber,
  formatPercentage,
  generateId,
  generateSlug,
  getRelativeTime,
  getStorage,
  getTimeSince,
  groupBy,
  hasRequiredFields,
  isValidEmail,
  isValidPhone,
  isValidURL,
  randomString,
  removeStorage,
  setStorage,
  shuffleArray,
  throttle,
  titleCase,
  truncateNumber,
  truncateText,
  unique,
} from '../../utils/helpers';

beforeEach(() => {
  localStorage.clear();
  // helpers resolve dates/numbers through the active i18n locale.
  localStorage.setItem('i18nextLng', 'en-US');
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe('helpers — dates', () => {
  it('formats dates with the active locale and default options', () => {
    expect(formatDate(new Date(2024, 0, 15))).toBe('Jan 15, 2024');
    expect(formatDate(new Date(2024, 0, 15), { month: 'long' })).toBe('January 15, 2024');
  });

  it('follows the stored i18n locale', () => {
    localStorage.setItem('i18nextLng', 'de-DE');
    expect(formatDate(new Date(2024, 0, 15))).toBe('15. Jan. 2024');
  });

  it('formats date-times and ISO input values', () => {
    expect(formatDateTime(new Date(2024, 0, 15, 13, 5))).toBe('1/15/2024, 1:05:00 PM');
    expect(formatDateISO(new Date(Date.UTC(2024, 0, 15, 12)))).toBe('2024-01-15');
  });

  it('produces relative times across all thresholds', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2024-06-01T12:00:00Z'));

    expect(getRelativeTime('2024-06-01T11:59:30Z')).toBe('just now');
    expect(getRelativeTime('2024-06-01T11:55:00Z')).toBe('5m ago');
    expect(getRelativeTime('2024-06-01T09:00:00Z')).toBe('3h ago');
    expect(getRelativeTime('2024-05-30T12:00:00Z')).toBe('2d ago');
    expect(getRelativeTime('2024-05-01T12:00:00Z')).toBe('May 1, 2024');
  });

  it('describes elapsed time in days, hours and minutes', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2024-06-01T12:00:00Z'));

    expect(getTimeSince('2024-06-01T11:59:00Z')).toBe('1 minute ago');
    expect(getTimeSince('2024-06-01T11:55:00Z')).toBe('5 minutes ago');
    expect(getTimeSince('2024-06-01T09:00:00Z')).toBe('3 hours ago');
    expect(getTimeSince('2024-05-30T12:00:00Z')).toBe('2 days ago');
  });
});

describe('helpers — numbers', () => {
  it('formats numbers and currency for the active locale', () => {
    expect(formatNumber(1234567.891)).toBe('1,234,567.891');
    expect(formatCurrency(1234.5)).toBe('$1,234.50');
    expect(formatCurrency(1234.5, 'EUR')).toBe('€1,234.50');
  });

  it('formats and calculates percentages', () => {
    expect(formatPercentage(12.3456)).toBe('12.3%');
    expect(formatPercentage(12.3456, 2)).toBe('12.35%');
    expect(calculatePercentage(1, 3)).toBe('33.33');
    expect(calculatePercentage(5, 0)).toBe(0);
  });

  it('truncates numbers to the requested precision', () => {
    expect(truncateNumber(1.239, 2)).toBe(1.24);
    expect(truncateNumber('3.14159', 3)).toBe(3.142);
  });
});

describe('helpers — strings', () => {
  it('generates URL-safe slugs', () => {
    expect(generateSlug('Hello, World! 2024')).toBe('hello-world-2024');
    expect(generateSlug('  Multiple   Spaces  ')).toBe('multiple-spaces');
    expect(generateSlug('--Leading--')).toBe('leading');
  });

  it('capitalizes and title-cases text', () => {
    expect(capitalize('hello')).toBe('Hello');
    expect(capitalize('hELLO')).toBe('HELLO');
    expect(capitalize('')).toBe('');
    expect(titleCase('hello WORLD from JS')).toBe('Hello World From Js');
  });

  it('truncates text only when needed', () => {
    expect(truncateText('abcdef', 3)).toBe('abc...');
    expect(truncateText('abc', 3)).toBe('abc');
    expect(truncateText('abcdef', 3, '!')).toBe('abc!');
    expect(truncateText('')).toBe('');
  });

  it('creates random strings and unique ids', () => {
    // Base-36 expansion of Math.random() is not fixed-width, so pin it.
    const randomSpy = vi.spyOn(Math, 'random').mockReturnValue(1e-16);

    expect(randomString(12)).toHaveLength(12);
    expect(randomString(12)).toMatch(/^[0-9a-z]{12}$/);
    expect(randomString()).toHaveLength(10);

    randomSpy.mockRestore();
    expect(generateId()).not.toBe(generateId());
  });
});

describe('helpers — arrays', () => {
  it('shuffles without mutating the source and preserves members', () => {
    const source = [1, 2, 3, 4, 5];
    const shuffled = shuffleArray(source);

    expect(shuffled).not.toBe(source);
    expect(source).toEqual([1, 2, 3, 4, 5]);
    expect([...shuffled].sort()).toEqual([1, 2, 3, 4, 5]);
  });

  it('groups items by key', () => {
    const grouped = groupBy(
      [
        { type: 'a', id: 1 },
        { type: 'b', id: 2 },
        { type: 'a', id: 3 },
      ],
      'type'
    );

    expect(grouped.a.map((item) => item.id)).toEqual([1, 3]);
    expect(grouped.b.map((item) => item.id)).toEqual([2]);
  });

  it('deduplicates by value or by key', () => {
    expect(unique([1, 2, 2, 3, 1])).toEqual([1, 2, 3]);
    expect(
      unique([{ id: 1, v: 'a' }, { id: 1, v: 'b' }, { id: 2, v: 'c' }], 'id').map((i) => i.v)
    ).toEqual(['a', 'c']);
  });

  it('chunks arrays and handles the remainder', () => {
    expect(chunkArray([1, 2, 3, 4, 5], 2)).toEqual([[1, 2], [3, 4], [5]]);
    expect(chunkArray([], 3)).toEqual([]);
    expect(chunkArray([1, 2], 10)).toEqual([[1, 2]]);
  });
});

describe('helpers — validation', () => {
  it('validates emails', () => {
    expect(isValidEmail('ada@example.com')).toBe(true);
    expect(isValidEmail('ada@example')).toBe(false);
    expect(isValidEmail('ada example.com')).toBe(false);
  });

  it('validates URLs', () => {
    expect(isValidURL('https://example.com/path')).toBe(true);
    expect(isValidURL('not a url')).toBe(false);
  });

  it('validates phone numbers', () => {
    expect(isValidPhone('5551234567')).toBe(true);
    expect(isValidPhone('(555) 123-4567')).toBe(true);
    expect(isValidPhone('12')).toBe(false);
    expect(isValidPhone('call-me')).toBe(false);
  });

  it('checks required fields, treating empty strings as missing', () => {
    expect(hasRequiredFields({ a: 1, b: 'x' }, ['a', 'b'])).toBe(true);
    expect(hasRequiredFields({ a: 0, b: '' }, ['a', 'b'])).toBe(false);
    expect(hasRequiredFields({}, ['a'])).toBe(false);
  });
});

describe('helpers — storage', () => {
  it('round-trips JSON values', () => {
    expect(setStorage('prefs', { theme: 'dark' })).toBe(true);
    expect(getStorage('prefs')).toEqual({ theme: 'dark' });
    expect(getStorage('missing', 'fallback')).toBe('fallback');
  });

  it('returns the default for corrupt JSON', () => {
    localStorage.setItem('broken', '{not-json');
    expect(getStorage('broken', null)).toBeNull();
  });

  it('removes single keys and clears only matching prefixes', () => {
    setStorage('lumicore_one', 1);
    setStorage('lumicore_two', 2);
    setStorage('other', 3);

    expect(removeStorage('lumicore_one')).toBe(true);
    expect(getStorage('lumicore_one')).toBeNull();

    expect(clearStorage('lumicore')).toBe(true);
    expect(getStorage('lumicore_two')).toBeNull();
    expect(getStorage('other')).toBe(3);
  });
});

describe('helpers — timing and UI', () => {
  it('debounces calls to the latest invocation', () => {
    vi.useFakeTimers();
    const fn = vi.fn();
    const debounced = debounce(fn, 300);

    debounced('first');
    vi.advanceTimersByTime(200);
    debounced('second');
    vi.advanceTimersByTime(299);
    expect(fn).not.toHaveBeenCalled();

    vi.advanceTimersByTime(1);
    expect(fn).toHaveBeenCalledTimes(1);
    expect(fn).toHaveBeenCalledWith('second');
  });

  it('throttles calls within the limit window', () => {
    vi.useFakeTimers();
    const fn = vi.fn();
    const throttled = throttle(fn, 300);

    throttled('a');
    throttled('b');
    expect(fn).toHaveBeenCalledTimes(1);
    expect(fn).toHaveBeenCalledWith('a');

    vi.advanceTimersByTime(300);
    throttled('c');
    expect(fn).toHaveBeenCalledTimes(2);
    expect(fn).toHaveBeenLastCalledWith('c');
  });

  it('copies text and reports clipboard failures', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText },
    });

    await expect(copyToClipboard('hello')).resolves.toEqual({ success: true, error: null });
    expect(writeText).toHaveBeenCalledWith('hello');

    writeText.mockRejectedValue(new Error('denied'));
    await expect(copyToClipboard('hello')).resolves.toEqual({
      success: false,
      error: 'denied',
    });

    delete navigator.clipboard;
  });

  it('joins class names and flattens nested arrays', () => {
    expect(cn('a', null, false, undefined, 'b', ['c', ['d']])).toBe('a b c d');
    expect(cn()).toBe('');
    expect(cn('')).toBe('');
  });

  it('mirrors named exports on the default export', () => {
    expect(helpers.cn).toBe(cn);
    expect(helpers.formatDate).toBe(formatDate);
    expect(helpers.formatCurrency).toBe(formatCurrency);
    expect(helpers.generateSlug).toBe(generateSlug);
    expect(helpers.debounce).toBe(debounce);
    expect(Object.keys(helpers)).toHaveLength(32);
    expect(Object.values(helpers).every((value) => typeof value === 'function')).toBe(true);
  });
});
