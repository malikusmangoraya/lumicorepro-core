/**
 * Tenant scoping helpers (multi-tenant isolation).
 *
 * The caller's organization is resolved with the same precedence the RBAC
 * middleware uses (`middleware/rbac.js`), so a route that already ran
 * `requireOrg` and one that only ran `protect` agree on the active tenant:
 *
 *   1. `req.orgCtx.org.id`       — set by `requireOrg` after verifying membership.
 *   2. `req.user.current_org_id` — the authenticated caller's own active org.
 *      A raw `x-org-id` header is never trusted for a logged-in user; they must
 *      switch orgs through `POST /api/orgs/:id/select` first.
 *   3. `x-org-id` header         — anonymous storefront requests only.
 *
 * A caller with no organization (anonymous visitor, or a user who has not
 * selected one yet) is restricted to legacy rows (`org_id IS NULL`), so tenant
 * rows are never exposed by omission.
 */
import { Op } from 'sequelize';

/**
 * Resolve the caller's organization id.
 * @param {object} req express request
 * @returns {number|null} organization id, or null for the legacy single-tenant scope
 */
export function callerOrgId(req) {
  const fromCtx = req?.orgCtx?.org?.id;
  if (fromCtx !== undefined && fromCtx !== null) return Number(fromCtx);

  if (req?.user) {
    const active = req.user.current_org_id;
    return active === undefined || active === null ? null : Number(active);
  }

  const header = req?.headers?.['x-org-id'];
  if (header === undefined || header === null || header === '') return null;
  const parsed = Number.parseInt(String(header), 10);
  return Number.isSafeInteger(parsed) && parsed > 0 ? parsed : null;
}

/**
 * Merge the caller's tenant filter into a Sequelize `where` clause.
 * @param {object} req express request
 * @param {object} [where] existing conditions
 * @returns {object} conditions pinned to the caller's org (`IS NULL` when unscoped)
 */
export function tenantWhere(req, where = {}) {
  const orgId = callerOrgId(req);
  return { ...where, org_id: orgId === null ? { [Op.is]: null } : orgId };
}

/**
 * Cache-key fragment so a cached payload can never be served across tenants.
 * @param {object} req express request
 * @returns {string} e.g. `org:12` or `org:none`
 */
export function tenantCacheKey(req) {
  const orgId = callerOrgId(req);
  return `org:${orgId === null ? 'none' : orgId}`;
}

export default { callerOrgId, tenantWhere, tenantCacheKey };
