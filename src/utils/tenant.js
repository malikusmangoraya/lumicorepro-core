/**
 * Tenant / subdomain utilities for multi-tenant SaaS hosting.
 */

const TENANT_HOSTS = ['localhost', '127.0.0.1'];

const extractSubdomain = (hostname) => {
  if (!hostname) return null;
  const parts = hostname.split('.');
  if (TENANT_HOSTS.includes(parts[0])) return null;
  if (parts.length < 2) return null;
  const candidate = parts[0];
  if (['www', 'app', 'api'].includes(candidate)) return null;
  return candidate;
};

/**
 * Detect the tenant slug from the current hostname (subdomain). Returns null
 * when running on the main app domain.
 * @returns {string|null}
 */
export const getTenantFromHost = () => {
  if (typeof window === 'undefined') return null;
  return extractSubdomain(window.location.hostname);
};

/**
 * Resolve the current tenant scope: explicit subdomain OR localStorage org.
 * Subdomain wins when present (deep-link into a tenant workspace).
 * @returns {{tenant: string|null, orgId: string|null}}
 */
export const getTenantContext = () => {
  const tenant = getTenantFromHost();
  if (tenant) return { tenant, orgId: tenant };
  if (typeof window === 'undefined') return { tenant: null, orgId: null };
  return { tenant: null, orgId: localStorage.getItem('active_org_id') || null };
};

/**
 * Build a tenant-aware absolute URL for a given path (used for invite links).
 */
export const tenantUrl = (path = '/') => {
  if (typeof window === 'undefined') return path;
  const { protocol, host } = window.location;
  return `${protocol}//${host}${path.startsWith('/') ? path : `/${path}`}`;
};