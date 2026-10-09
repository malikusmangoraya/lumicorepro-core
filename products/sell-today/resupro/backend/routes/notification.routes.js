import express from 'express';
import { Op } from 'sequelize';
import Notification from '../models/Notification.js';
import { protect, authorize } from '../middleware/auth.js';
import logger from '../utils/logger.js';

const router = express.Router();

/**
 * @swagger
 * /api/notifications:
 *   get:
 *     summary: Get user's notifications and unread count
 *     tags: [Notifications]
 *     security:
 *       - bearerAuth: []
 */
router.get('/', protect, async (req, res, next) => {
  try {
    const page = parseInt(req.query.page, 10) || 1;
    const limit = parseInt(req.query.limit, 10) || 20;
    const offset = (page - 1) * limit;

    const [unreadCount, { count: total, rows: notifications }] = await Promise.all([
      Notification.count({ where: { recipient: req.user.id, read: false } }),
      Notification.findAndCountAll({
        where: { recipient: req.user.id },
        order: [['createdAt', 'DESC']],
        limit,
        offset,
      }),
    ]);

    res.json({
      success: true,
      unreadCount,
      total,
      pagination: {
        page,
        limit,
        pages: Math.ceil(total / limit),
      },
      data: notifications,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/notifications:
 *   post:
 *     summary: Create notification and emit via socket (Admin/Internal)
 *     tags: [Notifications]
 *     security:
 *       - bearerAuth: []
 */
router.post('/', protect, async (req, res, next) => {
  try {
    const { recipientId, type, title, message, link, metadata } = req.body;

    const targetRecipient = recipientId ? parseInt(recipientId, 10) : req.user.id;

    const notification = await Notification.create({
      recipient: targetRecipient,
      type: type || 'info',
      title,
      message,
      link: link || '',
      metadata: metadata || {},
    });

    // Real-time socket delivery
    const io = req.app.get('io');
    if (io) {
      io.to(String(targetRecipient)).emit('new_notification', notification);
    }

    res.status(201).json({
      success: true,
      data: notification,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/notifications/read-all:
 *   patch:
 *     summary: Mark all user notifications as read
 *     tags: [Notifications]
 *     security:
 *       - bearerAuth: []
 */
// NOTE: This route MUST be declared before /:id to avoid Express treating
// "read-all" as a dynamic :id parameter.
router.patch('/read-all', protect, async (req, res, next) => {
  try {
    await Notification.update(
      { read: true, readAt: new Date() },
      { where: { recipient: req.user.id, read: false } }
    );

    res.json({
      success: true,
      message: 'All notifications marked as read',
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/notifications/broadcast:
 *   post:
 *     summary: Broadcast live social proof or announcement (Admin)
 *     tags: [Notifications]
 *     security:
 *       - bearerAuth: []
 */
router.post('/broadcast', protect, authorize('admin'), (req, res) => {
  const { event = 'announcement', payload } = req.body;

  const io = req.app.get('io');
  if (io) {
    io.emit(event, payload);
    logger.info(`Broadcasted event ${event} to all connected sockets`);
  }

  res.json({
    success: true,
    message: `Event ${event} broadcasted`,
  });
});

/**
 * @swagger
 * /api/notifications/{id}/read:
 *   patch:
 *     summary: Mark single notification as read
 *     tags: [Notifications]
 *     security:
 *       - bearerAuth: []
 */
router.patch('/:id/read', protect, async (req, res, next) => {
  try {
    const notification = await Notification.findOne({
      where: { id: req.params.id, recipient: req.user.id },
    });

    if (!notification) {
      return res.status(404).json({ success: false, error: 'Notification not found' });
    }

    await notification.update({ read: true, readAt: new Date() });

    res.json({
      success: true,
      data: notification,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @swagger
 * /api/notifications/{id}:
 *   delete:
 *     summary: Delete a notification
 *     tags: [Notifications]
 *     security:
 *       - bearerAuth: []
 */
router.delete('/:id', protect, async (req, res, next) => {
  try {
    const notification = await Notification.findOne({
      where: { id: req.params.id, recipient: req.user.id },
    });

    if (!notification) {
      return res.status(404).json({ success: false, error: 'Notification not found' });
    }

    await notification.destroy();

    res.json({
      success: true,
      message: 'Notification deleted successfully',
    });
  } catch (error) {
    next(error);
  }
});

export default router;
