/**
 * Multi-tenant RBAC middleware.
 *
 * - `requireOrg` resolves the active organization either from the
 *   `x-org-id` header or the user's `current_org_id`, verifies an active
 *   membership, and attaches `req.orgCtx = { org, membership, permissions }`.
 *   Returns 403 when the user has no membership in that org.
 * - `requirePermission(code)` gates a handler on a permission code. Global
 *   `admin` users bypass the check. Requires `requireOrg` to have run.
 */
import Organization from '../models/Organization.js';
import { getMembership, permissionCodes } from '../services/rbac.service.js';

export async function requireOrg(req, res, next) {
  try {
    const orgId = req.headers['x-org-id'] || req.user?.current_org_id;
    if (!orgId) {
      return res.status(403).json({ success: false, error: 'No active organization selected' });
    }

    const org = await Organization.findByPk(orgId);
    if (!org || org.deleted_at) {
      return res.status(404).json({ success: false, error: 'Organization not found' });
    }

    const membership = await getMembership(org.id, req.user.id);
    if (!membership) {
      return res
        .status(403)
        .json({ success: false, error: 'You are not a member of this organization' });
    }

    req.orgCtx = { org, membership, permissions: permissionCodes(membership) };
    next();
  } catch (error) {
    next(error);
  }
}

export function requirePermission(code) {
  return (req, res, next) => {
    if (req.user?.role === 'admin') return next();
    const has = (req.orgCtx?.permissions || []).includes(code);
    if (!has) {
      return res.status(403).json({ success: false, error: `Missing permission: ${code}` });
    }
    next();
  };
}

export function isOrgManager(req, res, next) {
  if (req.user?.role === 'admin') return next();
  const codes = new Set(req.orgCtx?.permissions || []);
  if (codes.has('org.manage') || codes.has('org.members.manage')) return next();
  return res
    .status(403)
    .json({ success: false, error: 'Organization management permission required' });
}

export default { requireOrg, requirePermission, isOrgManager };
