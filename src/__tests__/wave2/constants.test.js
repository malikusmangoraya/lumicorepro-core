import { describe, expect, it } from 'vitest';
import {
  APP_NAME,
  APP_VERSION,
  CategoryTypes,
  DateFormats,
  MaxLengths,
  Pagination,
  ROLES,
  SortOrders,
  STATUS,
} from '../../utils/constants';

describe('constants — app identity', () => {
  it('exposes the product name and a non-empty version', () => {
    expect(APP_NAME).toBe('LumicorePro Core');
    expect(typeof APP_VERSION).toBe('string');
    expect(APP_VERSION.length).toBeGreaterThan(0);
  });
});

describe('constants — roles and statuses', () => {
  it('defines the supported roles', () => {
    expect(ROLES).toEqual({
      ADMIN: 'admin',
      USER: 'user',
      EDITOR: 'editor',
      VIEWER: 'viewer',
    });
  });

  it('defines the lifecycle statuses', () => {
    expect(STATUS.ACTIVE).toBe('active');
    expect(STATUS.PENDING).toBe('pending');
    expect(STATUS.COMPLETED).toBe('completed');
    expect(STATUS.CANCELLED).toBe('cancelled');
    expect(STATUS.DRAFT).toBe('draft');
    expect(Object.values(STATUS)).toHaveLength(6);
  });
});

describe('constants — pagination and sorting', () => {
  it('defines sane pagination defaults', () => {
    expect(Pagination.DEFAULT_PAGE_SIZE).toBe(10);
    expect(Pagination.MAX_PAGE_SIZE).toBe(100);
    expect(Pagination.PAGE_SIZES).toEqual([10, 25, 50, 100]);
    expect(Pagination.PAGE_SIZES.every((size) => size <= Pagination.MAX_PAGE_SIZE)).toBe(true);
  });

  it('defines sort orders', () => {
    expect(SortOrders).toEqual({ ASC: 'asc', DESC: 'desc' });
  });
});

describe('constants — formats and limits', () => {
  it('defines date format patterns', () => {
    expect(DateFormats.DISPLAY).toBe('YYYY-MM-DD');
    expect(DateFormats.DATETIME).toBe('YYYY-MM-DD HH:mm:ss');
    expect(DateFormats.SHORT_DATE).toBe('MM/DD/YYYY');
    expect(DateFormats.LONG_DATE).toBe('MMMM DD, YYYY');
  });

  it('defines category types and field limits', () => {
    expect(CategoryTypes).toEqual({
      ECOMMERCE: 'ecommerce',
      DASHBOARD: 'dashboard',
      AI: 'ai',
      BUSINESS: 'business',
    });
    expect(MaxLengths.USERNAME).toBe(30);
    expect(MaxLengths.DESCRIPTION).toBe(500);
    expect(MaxLengths.PASSWORD).toBeGreaterThanOrEqual(64);
  });
});
