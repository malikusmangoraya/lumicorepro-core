import express from 'express';
import { Op } from 'sequelize';
import { body, validationResult } from 'express-validator';
import User from '../models/User.js';
import { protect, authorize } from '../middleware/auth.js';
import logger from '../utils/logger.js';

const router = express.Router();

/**
 * @swagger
 * /api/users/waitlist:
 *   get:
 *     summary: List users waiting on the beta waitlist (Admin only)
 *     tags: [Users]
 *     security:
 *       - bearerAuth: []
 */
router.get('/waitlist', protect, authorize('admin'), async (req, res, next) => {
  try {
    const { count: total, rows: users } = await User.findAndCountAll({
      where: { betaStatus: 'waitlist' },
      attributes: { exclude: ['password'] },
      order: [['createdAt', 'ASC']],
    });
    res.json({ success: true, data: { total, users } });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/users/{id}/approve-waitlist:
 *   post:
 *     summary: Approve a waitlist user for launch access (Admin only)
 *     tags: [Users]
 *     security:
 *       - bearerAuth: []
 */
router.post('/:id/approve-waitlist', protect, authorize('admin'), async (req, res, next) => {
  try {
    const user = await User.findByPk(req.params.id);
    if (!user) return res.status(404).json({ success: false, error: 'User not found' });

    await user.update({ betaStatus: 'active' });
    res.json({ success: true, message: 'User approved for launch access', data: { id: user.id } });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/users:
 *   get:
 *     summary: Get all users (Admin/Vendor only)
 *     tags: [Users]
 *     security:
 *       - bearerAuth: []
 */
router.get('/', protect, authorize('admin', 'vendor'), async (req, res, next) => {
  try {
    const page = parseInt(req.query.page, 10) || 1;
    const limit = parseInt(req.query.limit, 10) || 10;
    const offset = (page - 1) * limit;
    const { role, search } = req.query;

    const where = {};
    if (role) {
      where.role = role;
    }
    if (search) {
      where[Op.or] = [
        { name: { [Op.iLike]: `%${search}%` } },
        { email: { [Op.iLike]: `%${search}%` } },
      ];
    }

    const { count: total, rows: users } = await User.findAndCountAll({
      where,
      attributes: { exclude: ['password'] },
      order: [['createdAt', 'DESC']],
      limit,
      offset,
    });

    res.json({
      success: true,
      count: users.length,
      total,
      pagination: {
        page,
        limit,
        pages: Math.ceil(total / limit),
      },
      data: users,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/users/{id}:
 *   get:
 *     summary: Get single user by ID
 *     tags: [Users]
 *     security:
 *       - bearerAuth: []
 */
router.get('/:id', protect, async (req, res, next) => {
  try {
    const targetId = parseInt(req.params.id, 10);

    if (req.user.role !== 'admin' && req.user.id !== targetId) {
      return res.status(403).json({
        success: false,
        error: 'Not authorized to access this user',
      });
    }

    const user = await User.findByPk(targetId, {
      attributes: { exclude: ['password'] },
    });

    if (!user) {
      return res.status(404).json({ success: false, error: 'User not found' });
    }

    res.json({
      success: true,
      data: user,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/users:
 *   post:
 *     summary: Create new user (Admin only)
 *     tags: [Users]
 *     security:
 *       - bearerAuth: []
 */
router.post(
  '/',
  protect,
  authorize('admin'),
  [
    body('name').trim().notEmpty().withMessage('Name is required'),
    body('email').isEmail().normalizeEmail().withMessage('Valid email is required'),
    body('password').isLength({ min: 6 }).withMessage('Password must be at least 6 characters'),
  ],
  async (req, res, next) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ success: false, errors: errors.array() });
      }

      const { name, email, password, role, phone, address } = req.body;

      const existingUser = await User.findOne({ where: { email: email.toLowerCase().trim() } });
      if (existingUser) {
        return res
          .status(400)
          .json({ success: false, error: 'User with this email already exists' });
      }

      const user = await User.create({
        name,
        email: email.toLowerCase().trim(),
        password,
        role: role || 'user',
        phone: phone || null,
        address: address || null,
      });

      logger.info(`Admin created user: ${user.email}`);

      const userResponse = user.toJSON();
      delete userResponse.password;

      res.status(201).json({
        success: true,
        data: userResponse,
      });
    } catch (error) {
      next(error);
    }
  }
);

/**
 * @swagger
 * /api/users/{id}:
 *   put:
 *     summary: Update user
 *     tags: [Users]
 *     security:
 *       - bearerAuth: []
 */
router.put('/:id', protect, async (req, res, next) => {
  try {
    const targetId = parseInt(req.params.id, 10);

    if (req.user.role !== 'admin' && req.user.id !== targetId) {
      return res.status(403).json({
        success: false,
        error: 'Not authorized to update this user',
      });
    }

    const user = await User.findByPk(targetId);
    if (!user) {
      return res.status(404).json({ success: false, error: 'User not found' });
    }

    const allowedFields = ['name', 'phone', 'avatar', 'address', 'preferences'];
    if (req.user.role === 'admin') {
      allowedFields.push('role', 'isActive', 'isVerified', 'betaStatus');
    }

    const updates = {};
    allowedFields.forEach((field) => {
      if (req.body[field] !== undefined) {
        updates[field] = req.body[field];
      }
    });

    await user.update(updates);

    const userResponse = user.toJSON();
    delete userResponse.password;

    res.json({
      success: true,
      data: userResponse,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/users/{id}:
 *   delete:
 *     summary: Delete user (Admin only)
 *     tags: [Users]
 *     security:
 *       - bearerAuth: []
 */
router.delete('/:id', protect, authorize('admin'), async (req, res, next) => {
  try {
    const user = await User.findByPk(req.params.id, {
      attributes: { exclude: ['password'] },
    });

    if (!user) {
      return res.status(404).json({ success: false, error: 'User not found' });
    }

    await user.destroy();
    logger.info(`Admin deleted user: ${user.email} (${req.params.id})`);

    res.json({
      success: true,
      message: 'User deleted successfully',
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/users/{id}/status:
 *   patch:
 *     summary: Toggle user active status (Admin only)
 *     tags: [Users]
 *     security:
 *       - bearerAuth: []
 */
router.patch('/:id/status', protect, authorize('admin'), async (req, res, next) => {
  try {
    const user = await User.findByPk(req.params.id, {
      attributes: { exclude: ['password'] },
    });

    if (!user) {
      return res.status(404).json({ success: false, error: 'User not found' });
    }

    await user.update({ isActive: Boolean(req.body.isActive) });

    res.json({
      success: true,
      message: `User account ${user.isActive ? 'activated' : 'deactivated'}`,
      data: user,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/users/{id}/preferences:
 *   put:
 *     summary: Update user preferences
 *     tags: [Users]
 *     security:
 *       - bearerAuth: []
 */
router.put('/:id/preferences', protect, async (req, res, next) => {
  try {
    const targetId = parseInt(req.params.id, 10);

    if (req.user.id !== targetId && req.user.role !== 'admin') {
      return res.status(403).json({ success: false, error: 'Not authorized' });
    }

    const user = await User.findByPk(targetId);
    if (!user) {
      return res.status(404).json({ success: false, error: 'User not found' });
    }

    const { theme, language, notifications } = req.body;
    const currentPrefs = user.preferences || {};

    const updatedPrefs = {
      ...currentPrefs,
      ...(theme && { theme }),
      ...(language && { language }),
      ...(notifications && {
        notifications: { ...(currentPrefs.notifications || {}), ...notifications },
      }),
    };

    await user.update({ preferences: updatedPrefs });

    res.json({
      success: true,
      preferences: updatedPrefs,
    });
  } catch (error) {
    next(error);
  }
});

export default router;
