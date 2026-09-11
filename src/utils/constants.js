/**
 * Application constants
 * Shared configuration values across the app
 */

export const APP_NAME = 'LumicorePro Core';
export const APP_VERSION = import.meta.env.VITE_APP_VERSION || '1.0.0';

export const ROLES = {
  ADMIN: 'admin',
  USER: 'user',
  EDITOR: 'editor',
  VIEWER: 'viewer',
};

export const STATUS = {
  ACTIVE: 'active',
  INACTIVE: 'inactive',
  PENDING: 'pending',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled',
  DRAFT: 'draft',
};

export const Pagination = {
  DEFAULT_PAGE_SIZE: 10,
  MAX_PAGE_SIZE: 100,
  PAGE_SIZES: [10, 25, 50, 100],
};

export const SortOrders = {
  ASC: 'asc',
  DESC: 'desc',
};

export const DateFormats = {
  DISPLAY: 'YYYY-MM-DD',
  DATETIME: 'YYYY-MM-DD HH:mm:ss',
  TIME: 'HH:mm:ss',
  SHORT_DATE: 'MM/DD/YYYY',
  LONG_DATE: 'MMMM DD, YYYY',
};

export const CategoryTypes = {
  ECOMMERCE: 'ecommerce',
  DASHBOARD: 'dashboard',
  AI: 'ai',
  BUSINESS: 'business',
};

export const MaxLengths = {
  USERNAME: 30,
  PASSWORD: 100,
  TITLE: 100,
  DESCRIPTION: 500,
  BIO: 200,
};
