import express from 'express';
import vehicleService from '../services/vehicle.service.js';
import { protect, adminOnly } from '../middleware/auth.js';
import { recordAudit } from '../middleware/audit.js';
import logger from '../utils/logger.js';

/**
 * Vehicle inventory routes — mounted by `server.js` at /api/vehicles.
 *
 * Boundary rules:
 *   - `GET /` and `GET /:slug` are public and hard-scoped to active listings.
 *   - `GET /admin` and every write require an authenticated admin.
 *   - Withdrawal is a state change; the row is never deleted.
 *
 * The router stays thin: all query validation and write rules live in
 * `services/vehicle.service.js`, which raises typed errors this file maps to
 * status codes. Unexpected failures respond with a generic message and log
 * server-side, so no stack trace reaches a client.
 */
const router = express.Router();

const envelope = (message, data) => ({
  success: true,
  status: 200,
  message,
  data,
  timestamp: new Date().toISOString(),
});

function sendError(res, err, fallbackMessage) {
  const status = err?.status;

  if (status === 400 || err?.name === 'VehicleValidationError') {
    return res.status(400).json({
      success: false,
      status: 400,
      message: err?.message || 'Invalid vehicle request',
      errors: err?.errors || [],
      timestamp: new Date().toISOString(),
    });
  }

  if (status === 404 || err?.name === 'VehicleNotFoundError') {
    return res.status(404).json({
      success: false,
      status: 404,
      message: 'Vehicle not found',
      timestamp: new Date().toISOString(),
    });
  }

  if (status === 409 || err?.name === 'VehicleConflictError') {
    return res.status(409).json({
      success: false,
      status: 409,
      message: err?.message || 'Vehicle conflict',
      errors: err?.errors || [],
      timestamp: new Date().toISOString(),
    });
  }

  logger.error(`[vehicles] ${fallbackMessage}: ${err?.message}`);
  return res.status(500).json({
    success: false,
    status: 500,
    message: fallbackMessage,
    timestamp: new Date().toISOString(),
  });
}

/* ── Public: the showroom ────────────────────────────────────────────────── */

router.get('/', async (req, res) => {
  try {
    const result = await vehicleService.listVehicles(req.query, { includeInactive: false });
    res.json(envelope('Vehicles listed', result));
  } catch (err) {
    sendError(res, err, 'Could not load vehicles');
  }
});

/* ── Admin: full inventory, including inactive listings ──────────────────── */
/* Declared before '/:slug' so "admin" is never read as a vehicle slug. */

router.get('/admin', protect, adminOnly, async (req, res) => {
  try {
    const result = await vehicleService.listVehicles(req.query, { includeInactive: true });
    res.json(envelope('Inventory listed', result));
  } catch (err) {
    sendError(res, err, 'Could not load inventory');
  }
});

router.get('/admin/:id', protect, adminOnly, async (req, res) => {
  try {
    const vehicle = await vehicleService.getVehicleById(req.params.id);
    res.json(envelope('Vehicle loaded', vehicle));
  } catch (err) {
    sendError(res, err, 'Could not load vehicle');
  }
});

/* ── Public: one listing ─────────────────────────────────────────────────── */

router.get('/:slug', async (req, res) => {
  try {
    const vehicle = await vehicleService.getPublicVehicleBySlug(req.params.slug);
    res.json(envelope('Vehicle loaded', vehicle));
  } catch (err) {
    sendError(res, err, 'Could not load vehicle');
  }
});

/* ── Admin writes ────────────────────────────────────────────────────────── */

router.post('/', protect, adminOnly, async (req, res) => {
  try {
    const vehicle = await vehicleService.createVehicle(req.body);
    recordAudit(req, {
      action: 'vehicle.create',
      userId: req.user?.id ?? null,
      email: req.user?.email ?? null,
      meta: { vehicleId: vehicle.id, slug: vehicle.slug },
    });
    res.status(201).json({
      success: true,
      status: 201,
      message: 'Vehicle created',
      data: vehicle,
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    sendError(res, err, 'Could not create vehicle');
  }
});

router.patch('/:id', protect, adminOnly, async (req, res) => {
  try {
    const vehicle = await vehicleService.updateVehicle(req.params.id, req.body);
    recordAudit(req, {
      action: 'vehicle.update',
      userId: req.user?.id ?? null,
      email: req.user?.email ?? null,
      meta: { vehicleId: vehicle.id, slug: vehicle.slug },
    });
    res.json(envelope('Vehicle updated', vehicle));
  } catch (err) {
    sendError(res, err, 'Could not update vehicle');
  }
});

/**
 * DELETE withdraws the listing instead of removing the row, so inquiry and
 * reservation history keeps pointing at a real vehicle.
 */
router.delete('/:id', protect, adminOnly, async (req, res) => {
  try {
    const vehicle = await vehicleService.withdrawVehicle(req.params.id);
    recordAudit(req, {
      action: 'vehicle.withdraw',
      userId: req.user?.id ?? null,
      email: req.user?.email ?? null,
      meta: { vehicleId: vehicle.id, slug: vehicle.slug },
    });
    res.json(envelope('Vehicle withdrawn', vehicle));
  } catch (err) {
    sendError(res, err, 'Could not withdraw vehicle');
  }
});

export default router;
