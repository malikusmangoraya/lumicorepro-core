/**
 * RBAC service — multi-tenant roles & permissions.
 * Permissions are global (shared code set); roles are per-organization and
 * bind to global permissions through the `role_permissions` join table.
 */
import Membership from '../models/Membership.js';
import Role from '../models/Role.js';
import Permission from '../models/Permission.js';
import Organization from '../models/Organization.js';

export const PERMISSION = {
  ORG_VIEW: 'org.view',
  ORG_MANAGE: 'org.manage',
  MEMBERS_MANAGE: 'org.members.manage',
  PRODUCTS_MANAGE: 'products.manage',
  ORDERS_VIEW: 'orders.view',
  ANALYTICS_VIEW: 'analytics.view',
};

const DEFAULT_PERMISSIONS = [
  { code: PERMISSION.ORG_VIEW, name: 'View organization', description: 'See organization details' },
  {
    code: PERMISSION.ORG_MANAGE,
    name: 'Manage organization',
    description: 'Edit org name/settings',
  },
  {
    code: PERMISSION.MEMBERS_MANAGE,
    name: 'Manage members',
    description: 'Invite, change role, remove members',
  },
  {
    code: PERMISSION.PRODUCTS_MANAGE,
    name: 'Manage products',
    description: 'Create/update/delete products',
  },
  { code: PERMISSION.ORDERS_VIEW, name: 'View orders', description: 'Read organization orders' },
  {
    code: PERMISSION.ANALYTICS_VIEW,
    name: 'View analytics',
    description: 'Read usage and dashboards',
  },
];

/** Roles seeded into every new organization. */
const SYSTEM_ROLES = [
  { name: 'owner', permissions: Object.values(PERMISSION) },
  { name: 'admin', permissions: Object.values(PERMISSION) },
  {
    name: 'member',
    permissions: [PERMISSION.ORG_VIEW, PERMISSION.ORDERS_VIEW, PERMISSION.ANALYTICS_VIEW],
  },
];

/** Ensure global permission catalog exists. */
export async function seedPermissions() {
  for (const p of DEFAULT_PERMISSIONS) {
    await Permission.findOrCreate({ where: { code: p.code }, defaults: p });
  }
}

/** Create the default owner/admin/member roles for an org. */
export async function seedOrgRoles(orgId, transaction) {
  const permissions = await Permission.findAll();
  const byCode = new Map(permissions.map((p) => [p.code, p]));
  const created = {};
  for (const { name, permissions: codes } of SYSTEM_ROLES) {
    const [role] = await Role.findOrCreate({
      where: { org_id: orgId, name },
      defaults: { org_id: orgId, name, description: `System ${name} role`, is_system: true },
      transaction,
    });
    const perms = codes.map((c) => byCode.get(c)).filter(Boolean);
    if (perms.length) await role.setPermissions(perms, { transaction });
    created[name] = role;
  }
  return created;
}

/** Active membership (not revoked) of a user in an org, with role + permissions. */
export async function getMembership(orgId, userId) {
  const membership = await Membership.findOne({
    where: { org_id: orgId, user_id: userId, status: 'active' },
    include: [
      { model: Role, as: 'role', include: [{ model: Permission, through: { attributes: [] } }] },
    ],
  });
  return membership || null;
}

/** Permission codes for a membership (role-based). */
export function permissionCodes(membership) {
  const perms = membership?.role?.permissions || [];
  return perms.map((p) => p.code);
}

/**
 * Tenant-scoping helper: returns the `where` fragment that constrains a
 * tenant-resource query to one organization. Pass { allOrgs: true } (global
 * admin) to skip the filter.
 */
export function tenantScope(orgId, { global = false } = {}) {
  if (global) return {};
  return { org_id: orgId };
}

export { DEFAULT_PERMISSIONS, SYSTEM_ROLES, Organization };
