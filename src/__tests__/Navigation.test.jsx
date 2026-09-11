import { describe, it, expect } from 'vitest';
import { getNavByRole, isNavActive, getBreadcrumbs } from '../navigation/navItems';

describe('Navigation Module Utilities', () => {
  describe('getNavByRole', () => {
    it('should return public navigation items for standard user', () => {
      const nav = getNavByRole('user');
      expect(Array.isArray(nav)).toBe(true);
      expect(nav.some((item) => item.label === 'Home')).toBe(true);
      expect(nav.some((item) => item.label === 'Templates')).toBe(true);
    });
  });

  describe('isNavActive', () => {
    it('should correctly determine exact active path', () => {
      expect(isNavActive('/', '/')).toBe(true);
      expect(isNavActive('/templates', '/')).toBe(false);
      expect(isNavActive('/templates/ecommerce/ProductListing', '/templates/ecommerce')).toBe(true);
    });
  });

  describe('getBreadcrumbs', () => {
    it('should generate hierarchical breadcrumbs from path', () => {
      const crumbs = getBreadcrumbs('/templates/ecommerce/ProductListing');
      expect(crumbs.length).toBe(4);
      expect(crumbs[0]).toEqual({ label: 'Home', href: '/' });
      expect(crumbs[1].label).toBe('Templates');
    });
  });
});
