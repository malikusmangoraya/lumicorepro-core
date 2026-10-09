/**
 * Multi-tenant organization routes.
 * Mounted at /api/orgs behind `protect`. Organization-scoped routes resolve
 * the active org via `x-org-id` or the user's current_org_id.
 */
import express from 'express';
import jwt from 'jsonwebtoken';
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

// ── Public invite endpoints (registered before `protect`) ──────────────────
// These power the frontend InviteAccept page via email invite links.

const INVALID_INVITE = () => ({ success: false, error: 'Invite is invalid or has expired' });

function verifyInviteToken(token) {
  if (!token) return null;
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    if (decoded.purpose !== 'org_invite' || !decoded.orgId || !decoded.email) return null;
    return decoded;
  } catch {
    return null;
  }
}

/**
 * GET /api/orgs/invite/:token  — resolve an invite for the accept page.
 */
router.get('/invite/:token', async (req, res, next) => {
  try {
    const decoded = verifyInviteToken(req.params.token);
    if (!decoded) return res.status(400).json(INVALID_INVITE());

    const [org, role] = await Promise.all([
      Organization.findByPk(decoded.orgId, { attributes: ['id', 'name', 'slug'] }),
      Role.findByPk(decoded.roleId, { attributes: ['id', 'name'] }),
    ]);
    if (!org) return res.status(400).json(INVALID_INVITE());

    res.json({
      success: true,
      data: {
        orgId: org.id,
        orgName: org.name,
        email: decoded.email,
        role: role ? role.name : 'member',
        expiresAt: new Date(decoded.exp * 1000).toISOString(),
      },
    });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /api/orgs/invite/:token/accept — join the organization via invite token.
 * New users (no account for the invited email) can supply name + password to
 * be registered in the same call.
 */
router.post(
  '/invite/:token/accept',
  [
    body('name').optional().isString().isLength({ max: 120 }),
    body('password').optional().isString().isLength({ min: 6 }),
  ],
  async (req, res, next) => {
    try {
      const decoded = verifyInviteToken(req.params.token);
      if (!decoded) return res.status(400).json(INVALID_INVITE());

      const errors = validationResult(req);
      if (!errors.isEmpty())
        return res.status(400).json({ success: false, errors: errors.array() });

      const email = decoded.email.toLowerCase().trim();

      let user = await findUserByEmail(email);
      if (!user) {
        if (!req.body.password) {
          return res
            .status(400)
            .json({ success: false, error: 'Password is required to create your account' });
        }
        user = await User.create({
          name: (req.body.name || email.split('@')[0]).trim(),
          email,
          password: req.body.password,
          isActive: true,
        });
        user = await findUserByEmail(email);
      }
      if (!user)
        return res.status(500).json({ success: false, error: 'Failed to resolve account' });

      const [membership, created] = await Membership.findOrCreate({
        where: { org_id: decoded.orgId, user_id: user.id },
        defaults: {
          org_id: decoded.orgId,
          user_id: user.id,
          role_id: decoded.roleId || null,
          status: 'active',
          invited_by: null,
          joined_at: new Date(),
        },
      });
      if (!created) {
        await membership.update({
          status: 'active',
          role_id: decoded.roleId || membership.role_id,
          joined_at: membership.joined_at || new Date(),
        });
      }

      await setActiveOrg(user.id, decoded.orgId);

      const org = await Organization.findByPk(decoded.orgId, {
        attributes: ['id', 'name', 'slug'],
      });
      res.status(201).json({
        success: true,
        data: {
          org,
          membership: { id: membership.id, roleId: membership.role_id, status: membership.status },
          user: { id: user.id, name: user.name, email: user.email },
        },
      });
    } catch (error) {
      next(error);
    }
  }
);

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
 * POST /api/orgs/:id/members/invite  — generate a token-based invite link.
 * Unlike POST /:id/members (instant activation), this creates a `pending`
 * membership and returns a signed link the invitee opens to accept.
 */
router.post(
  '/:id/members/invite',
  requireOrg,
  requirePermission('org.members.manage'),
  [body('email').isEmail().normalizeEmail().withMessage('Valid email is required')],
  async (req, res, next) => {
    try {
      if (String(req.orgCtx.org.id) !== String(req.params.id)) {
        return res.status(403).json({ success: false, error: 'Cross-organization access denied' });
      }
      const errors = validationResult(req);
      if (!errors.isEmpty())
        return res.status(400).json({ success: false, errors: errors.array() });

      const email = req.body.email.toLowerCase().trim();
      const role = await Role.findOne({
        where: { org_id: req.orgCtx.org.id, name: req.body.role || 'member' },
      });
      if (!role)
        return res
          .status(400)
          .json({ success: false, error: `Unknown role: ${req.body.role || 'member'}` });

      const target = await findUserByEmail(email);

      const token = jwt.sign(
        { purpose: 'org_invite', orgId: req.orgCtx.org.id, roleId: role.id, email },
        process.env.JWT_SECRET,
        { expiresIn: '7d' }
      );

      if (target) {
        await Membership.findOrCreate({
          where: { org_id: req.orgCtx.org.id, user_id: target.id },
          defaults: {
            org_id: req.orgCtx.org.id,
            user_id: target.id,
            role_id: role.id,
            status: 'invited',
            invited_by: req.user.id,
            joined_at: null,
          },
        });
      }

      const frontend = (process.env.FRONTEND_URL || 'http://localhost:5173').replace(/\/+$/, '');
      const inviteUrl = `${frontend}/invite/${token}`;

      enqueue(QUEUES.EMAIL, {
        to: email,
        subject: `You were invited to ${req.orgCtx.org.name}`,
        html: `<h2>Invitation to ${req.orgCtx.org.name}</h2><p>${req.user.name || 'Someone'} invited you to <strong>${req.orgCtx.org.name}</strong> (role: ${role.name}).</p><p><a href="${inviteUrl}">Accept invitation</a></p>`,
      });

      recordAudit(req, {
        action: 'org.member.invite',
        userId: req.user.id,
        meta: { orgId: req.params.id, email, role: role.name, invite: true },
      });
      logger.info(`Invite link generated for ${email} to org ${req.params.id}`);

      res.status(201).json({ success: true, inviteUrl, expiresIn: '7d' });
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
