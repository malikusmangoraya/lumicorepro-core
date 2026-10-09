/**
 * Template update delivery routes.
 * ---------------------------------
 * Admin:
 *   POST /api/template-updates            publish a new version (admin)
 *   GET  /api/template-updates/product/:productId  version history (admin)
 * Buyer:
 *   GET  /api/template-updates/mine       updates for purchased templates
 *   GET  /api/template-updates/:productId/download  latest (or ?version=)
 */
import express from 'express';
import fs from 'fs';
import TemplateVersion from '../models/TemplateVersion.js';
import Product from '../models/Product.js';
import {
  publish,
  listForUser,
  resolveDownload,
  templateUpdatesDir,
} from '../services/templateUpdate.service.js';
import { protect, authorize } from '../middleware/auth.js';

const router = express.Router();

router.use(protect);

// ── Buyer endpoints ─────────────────────────────────────────────────────────
router.get('/mine', async (req, res, next) => {
  try {
    const updates = await listForUser(req.user.id);
    return res.json({ success: true, data: updates });
  } catch (err) {
    return next(err);
  }
});

router.get('/:productId/download', async (req, res, next) => {
  try {
    const { record, filePath } = await resolveDownload(
      req.user.id,
      req.params.productId,
      req.query.version || null,
    );
    res.setHeader('Content-Type', 'application/zip');
    res.setHeader('Content-Disposition', `attachment; filename="${record.file_name}"`);
    if (record.file_sha256) res.setHeader('X-File-Sha256', record.file_sha256);
    return fs.createReadStream(filePath).pipe(res);
  } catch (err) {
    return next(err);
  }
});

// ── Admin endpoints ─────────────────────────────────────────────────────────
router.post('/', authorize('admin'), async (req, res, next) => {
  try {
    const { productId, version, changelog, fileName } = req.body || {};
    const result = await publish({
      productId,
      version,
      changelog,
      fileName,
      publishedBy: req.user.id,
    });
    return res.status(201).json({
      success: true,
      data: { id: result.version.id, version: result.version.version, buyersNotified: result.buyersNotified },
    });
  } catch (err) {
    return next(err);
  }
});

router.get('/product/:productId', authorize('admin'), async (req, res, next) => {
  try {
    const versions = await TemplateVersion.findAll({
      where: { product_id: parseInt(req.params.productId, 10) },
      order: [['created_at', 'DESC']],
      raw: true,
    });
    return res.json({
      success: true,
      data: versions,
      updatesDir: templateUpdatesDir(),
    });
  } catch (err) {
    return next(err);
  }
});

export default router;
