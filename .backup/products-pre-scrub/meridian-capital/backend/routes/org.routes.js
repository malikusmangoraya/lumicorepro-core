/**
 * Multi-tenant organization routes.
 * Mounted at /api/orgs behind `protect`. Organization-scoped routes resolve
 * the active org via `x-org-id` or the user's current_org_id.
 */
import express from 'express';
import { body, validationResult } from 'express-validator';
import Organization from '../models/Organization.js';
import User from '../models/User.js';
import Membership from '../models/Membership.js';
import Role from '../models/Role.js';
import Permission from '../models/Permission.js';
import { seedPermissions, seedOrgRoles } from '../services/rbac.service.js';
import { requireOrg, requirePermission, isOrgManager } from '../middleware/rbac.js';
import { protect } from '../middleware/auth.js';
import { recordAudit } from '../middleware/audit.js';
import { enqueue, QUEUES } from '../services/queue/queue.service.js';
import logger from '../utils/logger.js';

const router = express.Router();

// All org endpoints require authentication
router.use(protect);

function slugify(name) {
  const base = name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 60);
  return `${base || 'org'}-${Date.now().toString(36)}`;
}

async function findUserByEmail(email) {
  const normEmail = email.toLowerCase().trim();
  try {
    return await User.scope('withPassword').findOne({ where: { email: normEmail } });
  } catch {
    return null;
  }
}

/** Ensure user has an active org selected after creation/join. */
async function setActiveOrg(userId, orgId) {
  await User.update({ current_org_id: orgId }, { where: { id: userId } });
}

/**
 * POST /api/orgs  — create an organization (creator becomes owner).
 */
router.post('/', async (req, res, next) => {
  try {
    await seedPermissions();
    const { name } = req.body;
    if (!name || !name.trim()) {
      return res.status(400).json({ success: false, error: 'Organization name is required' });
    }

    const org = await Organization.create({
      name: name.trim().slice(0, 255),
      slug: slugify(name),
      owner_id: req.user.id,
      settings: {},
    });

    const roles = await seedOrgRoles(org.id);

    await Membership.create({
      org_id: org.id,
      user_id: req.user.id,
      role_id: roles.owner.id,
      status: 'active',
      joined_at: new Date(),
    });

    await setActiveOrg(req.user.id, org.id);

    recordAudit(req, { action: 'org.create', userId: req.user.id, meta: { orgId: org.id } });
    logger.info(`Organization created: ${org.slug} by user ${req.user.id}`);

    res.status(201).json({ success: true, org, role: 'owner' });
  } catch (error) {
    if (error.name === 'SequelizeUniqueConstraintError') {
      return res.status(400).json({ success: false, error: 'Organization name already in use' });
    }
    next(error);
  }
});

/**
 * GET /api/orgs  — list organizations the user belongs to.
 */
router.get('/', async (req, res, next) => {
  try {
    const memberships = await Membership.findAll({
      where: { user_id: req.user.id },
      include: [
        { model: Organization, as: 'organization' },
        { model: Role, as: 'role' },
      ],
    });
    const orgs = memberships.map((m) => ({
      org: m.organization,
      role: m.role ? m.role.name : null,
      status: m.status,
    }));
    res.json({ success: true, orgs });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/orgs/current  — active org + my role + my permission codes.
 */
router.get('/current', requireOrg, (req, res) => {
  const { org, membership, permissions } = req.orgCtx;
  res.json({
    success: true,
    org,
    role: membership.role ? membership.role.name : null,
    permissions,
  });
});

/**
 * GET /api/orgs/permissions  — global permission catalog.
 */
router.get('/permissions', async (req, res, next) => {
  try {
    const perms = await Permission.findAll({ order: [['code', 'ASC']] });
    res.json({ success: true, permissions: perms });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/orgs/roles  — roles + granted permission codes for the active org.
 */
router.get('/roles', requireOrg, async (req, res, next) => {
  try {
    const roles = await Role.findAll({
      where: { org_id: req.orgCtx.org.id },
      include: [{ model: Permission, through: { attributes: [] } }],
      order: [['name', 'ASC']],
    });
    res.json({
      success: true,
      roles: roles.map((r) => ({
        id: r.id,
        name: r.name,
        is_system: r.is_system,
        description: r.description,
        permissions: r.permissions.map((p) => p.code),
      })),
    });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /api/orgs/:id/select  — switch the active organization for this user.
 */
router.post('/:id/select', async (req, res, next) => {
  try {
    const membership = await Membership.findOne({
      where: { org_id: req.params.id, user_id: req.user.id, status: 'active' },
    });
    if (!membership) {
      return res
        .status(403)
        .json({ success: false, error: 'You are not a member of this organization' });
    }
    await setActiveOrg(req.user.id, req.params.id);
    res.json({ success: true, message: 'Organization selected', orgId: Number(req.params.id) });
  } catch (error) {
    next(error);
  }
});

/**
 * PUT /api/orgs/:id  — rename org (owner/admin).
 */
router.put('/:id', requireOrg, isOrgManager, async (req, res, next) => {
  try {
    if (String(req.orgCtx.org.id) !== String(req.params.id)) {
      return res.status(403).json({ success: false, error: 'Cross-organization access denied' });
    }
    const name = req.body?.name;
    if (!name || !name.trim()) {
      return res.status(400).json({ success: false, error: 'Organization name is required' });
    }
    const updated = await req.orgCtx.org.update({ name: name.trim().slice(0, 255) });
    recordAudit(req, { action: 'org.update', userId: req.user.id, meta: { orgId: updated.id } });
    res.json({ success: true, org: updated });
  } catch (error) {
    next(error);
  }
});

/**
 * DELETE /api/orgs/:id  — soft-delete an org (owner/admin).
 */
router.delete('/:id', requireOrg, isOrgManager, async (req, res, next) => {
  try {
    if (String(req.orgCtx.org.id) !== String(req.params.id)) {
      return res.status(403).json({ success: false, error: 'Cross-organization access denied' });
    }
    await req.orgCtx.org.destroy(); // paranoid → sets deleted_at
    await setActiveOrg(req.user.id, null);
    recordAudit(req, { action: 'org.delete', userId: req.user.id, meta: { orgId: req.params.id } });
    res.json({ success: true, message: 'Organization removed' });
  } catch (error) {
    next(error);
  }
});

/* ═══════════════ Members ═══════════════ */

/**
 * GET /api/orgs/:id/members  — list members with user + role info.
 */
router.get('/:id/members', requireOrg, async (req, res, next) => {
  try {
    if (String(req.orgCtx.org.id) !== String(req.params.id)) {
      return res.status(403).json({ success: false, error: 'Cross-organization access denied' });
    }
    const memberships = await Membership.findAll({
      where: { org_id: req.orgCtx.org.id },
      include: [{ model: Role, as: 'role' }],
      order: [['joined_at', 'ASC']],
    });
    const users = await Promise.all(
      memberships.map(async (m) => {
        const u = await User.findByPk(m.user_id);
        return {
          id: m.id,
          userId: m.user_id,
          name: u ? u.name : null,
          email: u ? u.email : null,
          role: m.role ? m.role.name : null,
          status: m.status,
          joinedAt: m.joined_at,
        };
      })
    );
    res.json({ success: true, members: users });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /api/orgs/:id/members  — invite an existing user by email.
 */
router.post(
  '/:id/members',
  requireOrg,
  requirePermission('org.members.manage'),
  [
    body('email').isEmail().normalizeEmail().withMessage('Valid email is required'),
    body('role').optional().isString(),
  ],
  async (req, res, next) => {
    try {
      if (String(req.orgCtx.org.id) !== String(req.params.id)) {
        return res.status(403).json({ success: false, error: 'Cross-organization access denied' });
      }
      const errors = validationResult(req);
      if (!errors.isEmpty())
        return res.status(400).json({ success: false, errors: errors.array() });

      const email = req.body.email.toLowerCase().trim();
      const roleName = req.body.role || 'member';

      const role = await Role.findOne({ where: { org_id: req.orgCtx.org.id, name: roleName } });
      if (!role)
        return res.status(400).json({ success: false, error: `Unknown role: ${roleName}` });

      const target = await findUserByEmail(email);
      if (!target) {
        return res.status(404).json({ success: false, error: 'No account found for this email' });
      }

      await Membership.findOrCreate({
        where: { org_id: req.orgCtx.org.id, user_id: target.id },
        defaults: {
          org_id: req.orgCtx.org.id,
          user_id: target.id,
          role_id: role.id,
          status: 'active',
          invited_by: req.user.id,
          joined_at: new Date(),
        },
      });

      enqueue(QUEUES.EMAIL, {
        to: email,
        subject: `You were invited to ${req.orgCtx.org.name}`,
        html: `<h2>Invitation</h2><p>${req.user.name || 'Someone'} invited you to the <strong>${req.orgCtx.org.name}</strong> organization (role: ${roleName}).</p>`,
      });

      recordAudit(req, {
        action: 'org.member.invite',
        userId: req.user.id,
        meta: { orgId: req.params.id, email, role: roleName },
      });
      logger.info(`Member ${email} invited to org ${req.params.id}`);
      res.status(201).json({ success: true, message: `Invitation sent to ${email}` });
    } catch (error) {
      next(error);
    }
  }
);

/**
 * PUT /api/orgs/:id/members/:userId  — change a member's role.
 */
router.put(
  '/:id/members/:userId',
  requireOrg,
  requirePermission('org.members.manage'),
  async (req, res, next) => {
    try {
      if (String(req.orgCtx.org.id) !== String(req.params.id)) {
        return res.status(403).json({ success: false, error: 'Cross-organization access denied' });
      }
      const membership = await Membership.findOne({
        where: { org_id: req.orgCtx.org.id, user_id: req.params.userId },
      });
      if (!membership)
        return res.status(404).json({ success: false, error: 'Membership not found' });

      const roleName = req.body?.role;
      if (roleName) {
        const role = await Role.findOne({ where: { org_id: req.orgCtx.org.id, name: roleName } });
        if (!role)
          return res.status(400).json({ success: false, error: `Unknown role: ${roleName}` });
        await membership.update({ role_id: role.id });
      }
      const status = req.body?.status;
      if (status && ['active', 'invited', 'revoked'].includes(status)) {
        if (status === 'active' && !membership.joined_at) {
          await membership.update({ status, joined_at: new Date() });
        } else {
          await membership.update({ status });
        }
      }

      recordAudit(req, {
        action: 'org.member.update',
        userId: req.user.id,
        meta: { orgId: req.params.id, targetUserId: req.params.userId, ...req.body },
      });
      res.json({ success: true, message: 'Membership updated' });
    } catch (error) {
      next(error);
    }
  }
);

/**
 * DELETE /api/orgs/:id/members/:userId  — revoke a member.
 */
router.delete(
  '/:id/members/:userId',
  requireOrg,
  requirePermission('org.members.manage'),
  async (req, res, next) => {
    try {
      if (String(req.orgCtx.org.id) !== String(req.params.id)) {
        return res.status(403).json({ success: false, error: 'Cross-organization access denied' });
      }
      if (String(req.params.userId) === String(req.user.id)) {
        return res.status(400).json({ success: false, error: 'Cannot revoke your own membership' });
      }
      const membership = await Membership.findOne({
        where: { org_id: req.orgCtx.org.id, user_id: req.params.userId },
      });
      if (!membership)
        return res.status(404).json({ success: false, error: 'Membership not found' });
      await membership.update({ status: 'revoked' });

      recordAudit(req, {
        action: 'org.member.remove',
        userId: req.user.id,
        meta: { orgId: req.params.id, targetUserId: req.params.userId },
      });
      res.json({ success: true, message: 'Membership revoked' });
    } catch (error) {
      next(error);
    }
  }
);

export default router;
