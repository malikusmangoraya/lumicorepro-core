import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AppContext } from '../../context/AppContext';
import { OrgProvider, useOrg } from '../../context/OrgContext';
import orgService from '../../services/orgs';

vi.mock('../../services/orgs', () => ({
  default: {
    list: vi.fn(),
    create: vi.fn(),
    current: vi.fn(),
    select: vi.fn(),
  },
}));

const orgs = [
  { org: { id: 1, name: 'Alpha' }, role: 'owner' },
  { org: { id: 2, name: 'Beta' }, role: 'member' },
];

const makeWrapper =
  (isAuthenticated = true) =>
  ({ children }) => (
    <AppContext.Provider value={{ isAuthenticated }}>
      <OrgProvider>{children}</OrgProvider>
    </AppContext.Provider>
  );

beforeEach(() => {
  localStorage.clear();
  vi.clearAllMocks();
  orgService.list.mockResolvedValue({ data: { orgs } });
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('OrgContext — loading organizations', () => {
  it('does nothing when the user is not authenticated', async () => {
    const { result } = renderHook(() => useOrg(), { wrapper: makeWrapper(false) });

    await act(async () => {
      await Promise.resolve();
    });

    expect(orgService.list).not.toHaveBeenCalled();
    expect(result.current.orgs).toEqual([]);
    expect(result.current.current).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it('loads organizations and restores the stored active org', async () => {
    localStorage.setItem('active_org_id', '2');
    orgService.current.mockResolvedValue({
      data: { org: { id: 2, name: 'Beta' }, permissions: ['org.manage'] },
    });

    const { result } = renderHook(() => useOrg(), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(orgService.list).toHaveBeenCalledTimes(1);
    expect(result.current.orgs).toEqual(orgs);
    expect(result.current.current).toEqual({ id: 2, name: 'Beta' });
    expect(result.current.permissions).toEqual(['org.manage']);
    expect(result.current.error).toBeNull();
    expect(localStorage.getItem('active_org_id')).toBe('2');
  });

  it('defaults to the first org when the server has no active org', async () => {
    orgService.current.mockResolvedValue({ data: {} });

    const { result } = renderHook(() => useOrg(), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.current).toEqual(orgs[0].org);
    expect(result.current.permissions).toEqual([]);
    expect(localStorage.getItem('active_org_id')).toBe('1');
  });

  it('falls back to the first org when the stored id is unknown', async () => {
    localStorage.setItem('active_org_id', '999');
    orgService.current.mockResolvedValue({ data: {} });

    const { result } = renderHook(() => useOrg(), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.current).toEqual(orgs[0].org);
    expect(localStorage.getItem('active_org_id')).toBe('1');
  });

  it('treats a 403 current-org response as "no active org", not an error', async () => {
    orgService.list.mockResolvedValue({ data: { orgs: [] } });
    orgService.current.mockRejectedValue({ response: { status: 403 } });

    const { result } = renderHook(() => useOrg(), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.current).toBeNull();
    expect(result.current.permissions).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it('surfaces non-403 failures with the server message', async () => {
    orgService.current.mockRejectedValue({
      response: { status: 500, data: { error: 'Organization service unavailable' } },
    });

    const { result } = renderHook(() => useOrg(), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('Organization service unavailable');
    expect(result.current.loading).toBe(false);
  });

  it('uses err.message when the failure has no response body', async () => {
    orgService.current.mockRejectedValue(new Error('Network down'));

    const { result } = renderHook(() => useOrg(), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('Network down');
  });
});

describe('OrgContext — org actions', () => {
  it('creates an org, persists it as active and refreshes the list', async () => {
    orgService.create.mockResolvedValue({ data: { org: { id: 7, name: 'Gamma' } } });
    orgService.current.mockResolvedValue({
      data: { org: { id: 7, name: 'Gamma' }, permissions: [] },
    });

    const { result } = renderHook(() => useOrg(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.loading).toBe(false));

    let created;
    await act(async () => {
      created = await result.current.createOrg('Gamma');
    });

    expect(orgService.create).toHaveBeenCalledWith('Gamma');
    expect(created).toEqual({ id: 7, name: 'Gamma' });
    expect(localStorage.getItem('active_org_id')).toBe('7');
    expect(orgService.list).toHaveBeenCalledTimes(2);
    expect(result.current.current).toEqual({ id: 7, name: 'Gamma' });
  });

  it('switches org, persists the id and tolerates a failed select call', async () => {
    orgService.current.mockResolvedValue({
      data: { org: { id: 2, name: 'Beta' }, permissions: [] },
    });
    orgService.select.mockRejectedValue(new Error('offline'));

    const { result } = renderHook(() => useOrg(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.switchOrg(2);
    });

    expect(orgService.select).toHaveBeenCalledWith(2);
    expect(localStorage.getItem('active_org_id')).toBe('2');
    expect(result.current.current).toEqual({ id: 2, name: 'Beta' });
    expect(orgService.list).toHaveBeenCalledTimes(2);
  });

  it('exposes permission checks and manager status', async () => {
    orgService.current.mockResolvedValue({
      data: { org: { id: 1, name: 'Alpha' }, permissions: ['org.members.manage'] },
    });

    const { result } = renderHook(() => useOrg(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.has('org.members.manage')).toBe(true);
    expect(result.current.has('org.billing.manage')).toBe(false);
    expect(result.current.isManager).toBe(true);
  });

  it('is not a manager without an org management permission', async () => {
    orgService.current.mockResolvedValue({
      data: { org: { id: 2, name: 'Beta' }, permissions: ['org.view'] },
    });

    const { result } = renderHook(() => useOrg(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.isManager).toBe(false);
  });
});

describe('useOrg guard', () => {
  it('throws when used outside OrgProvider', () => {
    expect(() => renderHook(() => useOrg())).toThrow('useOrg must be used within OrgProvider');
  });
});
