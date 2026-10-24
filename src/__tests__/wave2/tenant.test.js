import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { getTenantContext, getTenantFromHost, tenantUrl } from '../../utils/tenant';

const realLocation = window.location;

function setHostname(hostname, protocol = 'https:') {
  Object.defineProperty(window, 'location', {
    configurable: true,
    value: {
      hostname,
      protocol,
      host: hostname,
      origin: `${protocol}//${hostname}`,
      href: `${protocol}//${hostname}/`,
    },
  });
}

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  Object.defineProperty(window, 'location', { configurable: true, value: realLocation });
});

describe('getTenantFromHost', () => {
  it('returns null on the local development host', () => {
    setHostname('localhost');
    expect(getTenantFromHost()).toBeNull();
  });

  it('extracts a tenant subdomain from a production host', () => {
    setHostname('acme.example.com');
    expect(getTenantFromHost()).toBe('acme');

    setHostname('shop.eu.example.com');
    expect(getTenantFromHost()).toBe('shop');
  });

  it('ignores reserved subdomains and bare hostnames', () => {
    ['www.example.com', 'app.example.com', 'api.example.com'].forEach((hostname) => {
      setHostname(hostname);
      expect(getTenantFromHost()).toBeNull();
    });

    setHostname('single-label');
    expect(getTenantFromHost()).toBeNull();
  });
});

describe('getTenantContext', () => {
  it('prefers the subdomain tenant over the stored org', () => {
    localStorage.setItem('active_org_id', '42');
    setHostname('acme.example.com');

    expect(getTenantContext()).toEqual({ tenant: 'acme', orgId: 'acme' });
  });

  it('falls back to the persisted active org', () => {
    localStorage.setItem('active_org_id', '42');
    setHostname('app.example.com');

    expect(getTenantContext()).toEqual({ tenant: null, orgId: '42' });
  });

  it('returns nulls when there is no tenant and no stored org', () => {
    setHostname('localhost');

    expect(getTenantContext()).toEqual({ tenant: null, orgId: null });
  });
});

describe('tenantUrl', () => {
  it('builds an absolute URL for the current host', () => {
    setHostname('shop.example.com');

    expect(tenantUrl('/settings')).toBe('https://shop.example.com/settings');
    expect(tenantUrl('settings')).toBe('https://shop.example.com/settings');
    expect(tenantUrl()).toBe('https://shop.example.com/');
  });

  it('keeps the current protocol', () => {
    setHostname('localhost:5173', 'http:');

    expect(tenantUrl('/invite/abc')).toBe('http://localhost:5173/invite/abc');
  });
});
