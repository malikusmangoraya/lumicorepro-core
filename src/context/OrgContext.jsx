/**
 * OrgContext — multi-tenant organization state.
 *
 * Loads the user's organizations, tracks the active one (persisted in
 * localStorage as `active_org_id` and mirrored to the server via
 * current_org_id), and exposes permission codes for the active org so
 * components can render role-aware UI.
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useAppContext } from './AppContext';
import orgService from '../services/orgs';

const OrgContext = createContext(null);

export function useOrg() {
  const ctx = useContext(OrgContext);
  if (!ctx) throw new Error('useOrg must be used within OrgProvider');
  return ctx;
}

export function OrgProvider({ children }) {
  const { isAuthenticated } = useAppContext();
  const [orgs, setOrgs] = useState([]);
  const [current, setCurrent] = useState(null);
  const [permissions, setPermissions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    setError(null);
    try {
      const res = await orgService.list();
      const list = res.data?.orgs || [];
      setOrgs(list);

      const storedId = localStorage.getItem('active_org_id');
      let active = storedId
        ? list.find((o) => String(o.org?.id) === String(storedId))
        : undefined;
      if (!active && list.length) {
        active = list[0];
        localStorage.setItem('active_org_id', String(active.org.id));
      }

      const currentRes = await orgService.current();
      const cur = currentRes.data?.org;
      const perms = currentRes.data?.permissions || [];
      if (cur) {
        setCurrent(cur);
        setPermissions(perms);
        localStorage.setItem('active_org_id', String(cur.id));
      } else {
        setCurrent(active?.org || null);
        setPermissions(active?.org ? [] : []);
      }
    } catch (err) {
      if (err.response?.status === 403) {
        // No active org selected — that's fine, user can create/join one.
        setCurrent(null);
        setPermissions([]);
      } else {
        setError(err.response?.data?.error || err.message || 'Failed to load organizations');
      }
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    refresh();
  }, [refresh, isAuthenticated]);

  const createOrg = useCallback(
    async (name) => {
      const res = await orgService.create(name);
      const org = res.data?.org;
      localStorage.setItem('active_org_id', String(org.id));
      await refresh();
      return org;
    },
    [refresh]
  );

  const switchOrg = useCallback(
    async (orgId) => {
      localStorage.setItem('active_org_id', String(orgId));
      await orgService.select(orgId).catch(() => {});
      await refresh();
    },
    [refresh]
  );

  const has = useCallback(
    (code) => permissions.includes(code),
    [permissions]
  );

  const value = useMemo(
    () => ({
      orgs,
      current,
      permissions,
      loading,
      error,
      refresh,
      createOrg,
      switchOrg,
      has,
      isManager: has('org.members.manage') || has('org.manage'),
    }),
    [orgs, current, permissions, loading, error, refresh, createOrg, switchOrg, has]
  );

  return <OrgContext.Provider value={value}>{children}</OrgContext.Provider>;
}

export default OrgContext;