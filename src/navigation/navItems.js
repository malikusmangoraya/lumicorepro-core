import {
  mainNavLinks,
  dashboardNavLinks,
  templateCategories,
  userDropdownNav,
} from './navigationConfig';

/**
 * Filter navigation links based on user role
 * @param {string} role - 'admin' | 'vendor' | 'user' | null
 * @returns {Array} Filtered navigation links
 */
export const getNavByRole = (role = 'user') => {
  return mainNavLinks.filter((link) => {
    if (!link.roles) return true;
    return link.roles.includes(role);
  });
};

/**
 * Filter dashboard navigation sidebar items based on user role
 * @param {string} role - 'admin' | 'vendor' | 'user'
 * @returns {Array} Filtered dashboard groups and items
 */
export const getDashboardNavByRole = (role = 'user') => {
  return dashboardNavLinks
    .map((group) => ({
      ...group,
      items: group.items.filter((item) => {
        if (!item.roles) return true;
        return item.roles.includes(role);
      }),
    }))
    .filter((group) => group.items.length > 0);
};

/**
 * Check if the current pathname matches or is a parent of nav link
 * @param {string} currentPath - Current router pathname
 * @param {string} linkHref - Nav item href
 * @returns {boolean}
 */
export const isNavActive = (currentPath, linkHref) => {
  if (linkHref === '/') {
    return currentPath === '/';
  }
  return currentPath.startsWith(linkHref);
};

/**
 * Resolve breadcrumbs from current pathname
 * @param {string} pathname - Current window pathname
 * @returns {Array<{ label: string, href: string }>}
 */
export const getBreadcrumbs = (pathname) => {
  if (!pathname || pathname === '/') {
    return [{ label: 'Home', href: '/' }];
  }

  const parts = pathname.split('/').filter(Boolean);
  const breadcrumbs = [{ label: 'Home', href: '/' }];

  let accumulatedPath = '';
  parts.forEach((part) => {
    accumulatedPath += `/${part}`;
    // Format label: camelCase or kebab-case to Title Case
    const label = part
      .replace(/([A-Z])/g, ' $1')
      .replace(/-/g, ' ')
      .trim();

    breadcrumbs.push({
      label: label.charAt(0).toUpperCase() + label.slice(1),
      href: accumulatedPath,
    });
  });

  return breadcrumbs;
};
