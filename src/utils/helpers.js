/**
 * Utility helper functions
 * LumicorePro Core - Common utilities for data formatting, validation, and manipulation
 */

// ==================== Date/Time Helpers ====================

/**
 * Resolve the active locale from i18n (import-safe, no circular deps).
 * i18next-browser-languagedetector persists the language under `i18nextLng`.
 * Falls back to the browser default when unavailable.
 */
const resolveLocale = () => {
  try {
    if (typeof window === 'undefined') return undefined;
    const lang = window.localStorage?.getItem('i18nextLng');
    return lang && lang !== 'undefined' && lang !== 'cimode' ? lang.replace('_', '-') : undefined;
  } catch {
    return undefined;
  }
};

/** Format date to readable string (locale-aware via active i18n language) */
export const formatDate = (date, options = {}) => {
  const defaultOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...options,
  };
  const locale = resolveLocale();
  return new Date(date).toLocaleDateString(locale, defaultOptions);
};

/** Format date and time (locale-aware) */
export const formatDateTime = (date) => {
  return new Date(date).toLocaleString(resolveLocale());
};

/** Get relative time (e.g., "2 hours ago") */
export const getRelativeTime = (date) => {
  const now = new Date();
  const then = new Date(date);
  const diff = Math.floor((now - then) / 1000);

  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
  return formatDate(date);
};

/** Format date for input fields */
export const formatDateISO = (date) => {
  return new Date(date).toISOString().split('T')[0];
};

/** Get time since */
export const getTimeSince = (date) => {
  const minutes = Math.floor((new Date() - new Date(date)) / 60000);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
  if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
  return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
};

// ==================== Number Helpers ====================

/** Format number with commas (locale-aware) */
export const formatNumber = (num) => {
  return new Intl.NumberFormat(resolveLocale()).format(num);
};

/** Format currency (locale-aware) */
export const formatCurrency = (amount, currency = 'USD') => {
  return new Intl.NumberFormat(resolveLocale(), {
    style: 'currency',
    currency,
  }).format(amount);
};

/** Format percentage */
export const formatPercentage = (value, decimals = 1) => {
  return `${Number(value).toFixed(decimals)}%`;
};

/** Calculate percentage */
export const calculatePercentage = (part, total) => {
  if (total === 0) return 0;
  return ((part / total) * 100).toFixed(2);
};

/** Truncate number to decimal places */
export const truncateNumber = (num, decimals = 2) => {
  return Number(Number(num).toFixed(decimals));
};

// ==================== String Helpers ====================

/** Generate slug from string */
export const generateSlug = (str) => {
  return str
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
};

/** Capitalize first letter */
export const capitalize = (str) => {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
};

/** Title case */
export const titleCase = (str) => {
  return str.replace(/\w\S*/g, (txt) => {
    return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
  });
};

/** Truncate text */
export const truncateText = (text, length = 100, suffix = '...') => {
  if (!text) return '';
  if (text.length <= length) return text;
  return text.slice(0, length) + suffix;
};

/** Generate random string */
export const randomString = (length = 10) => {
  return Math.random()
    .toString(36)
    .substring(2, 2 + length);
};

/** Generate random ID */
export const generateId = () => {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
};

// ==================== Array Helpers ====================

/** Shuffle array */
export const shuffleArray = (array) => {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
};

/** Group array by key */
export const groupBy = (array, key) => {
  return array.reduce((groups, item) => {
    const group = item[key];
    groups[group] = groups[group] || [];
    groups[group].push(item);
    return groups;
  }, {});
};

/** Remove duplicates from array */
export const unique = (arr, key = null) => {
  if (key) {
    return arr.filter((item, index, self) => index === self.findIndex((t) => t[key] === item[key]));
  }
  return [...new Set(arr)];
};

/** Chunk array into smaller arrays */
export const chunkArray = (array, size = 10) => {
  return Array.from({ length: Math.ceil(array.length / size) }, (_, i) =>
    array.slice(i * size, i * size + size)
  );
};

// ==================== Validation Helpers ====================

/** Validate email */
export const isValidEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
};

/** Validate URL */
export const isValidURL = (url) => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

/** Validate phone number */
export const isValidPhone = (phone) => {
  const re = /^[+]?(?:[(]?[0-9]{3}[)]?[-\s.]?[0-9]{3}[-\s.]?[0-9]{4,6})$/;
  return re.test(phone);
};

/** Check if required fields exist */
export const hasRequiredFields = (obj, fields) => {
  return fields.every((field) => obj[field] !== undefined && obj[field] !== '');
};

// ==================== Storage Helpers ====================

/** Safe localStorage get */
export const getStorage = (key, defaultValue = null) => {
  try {
    const item = window.localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch {
    return defaultValue;
  }
};

/** Safe localStorage set */
export const setStorage = (key, value) => {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
};

/** Safe localStorage remove */
export const removeStorage = (key) => {
  try {
    window.localStorage.removeItem(key);
    return true;
  } catch {
    return false;
  }
};

/** Clear all app storage */
export const clearStorage = (prefix = 'lumicore') => {
  try {
    Object.keys(localStorage).forEach((key) => {
      if (key.startsWith(prefix)) {
        localStorage.removeItem(key);
      }
    });
    return true;
  } catch {
    return false;
  }
};

// ==================== UI Helpers ====================

/** Debounce function */
export const debounce = (func, wait = 300) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

/** Throttle function */
export const throttle = (func, limit = 300) => {
  let inThrottle;
  return function (...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};

/** Copy to clipboard */
export const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    return { success: true, error: null };
  } catch (err) {
    return { success: false, error: err.message };
  }
};

// ==================== CSS Utilities ====================

/** Merge class names; filters falsy values and flattens nested arrays. */
export const cn = (...classes) => {
  return classes
    .flat(Infinity)
    .filter((c) => typeof c === 'string' && c.length > 0)
    .join(' ');
};

// ==================== Export All ====================
export default {
  cn,
  formatDate,
  formatDateTime,
  getRelativeTime,
  formatDateISO,
  getTimeSince,
  formatNumber,
  formatCurrency,
  formatPercentage,
  calculatePercentage,
  truncateNumber,
  generateSlug,
  capitalize,
  titleCase,
  truncateText,
  randomString,
  generateId,
  shuffleArray,
  groupBy,
  unique,
  chunkArray,
  isValidEmail,
  isValidURL,
  isValidPhone,
  hasRequiredFields,
  getStorage,
  setStorage,
  removeStorage,
  clearStorage,
  debounce,
  throttle,
  copyToClipboard,
};
