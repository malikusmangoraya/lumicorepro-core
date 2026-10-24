import express from 'express';
import { Op } from 'sequelize';
import Booking from '../models/Booking.js';
import Doctor from '../models/Doctor.js';
import Service from '../models/Service.js';
import User from '../models/User.js';
import { protect } from '../middleware/auth.js';
import { enqueue, QUEUES } from '../services/queue/queue.service.js';
import logger from '../utils/logger.js';
import { sequelize } from '../config/database.js';
import { TIME_PATTERN, isValidDate } from '../utils/reservationSlot.js';

const router = express.Router();

/** Minutes since midnight for an `HH:MM` string; null when malformed. */
const timeToMinutes = (value) => {
  if (!TIME_PATTERN.test(String(value))) return null;
  const [hours, minutes] = String(value).split(':').map(Number);
  return hours * 60 + minutes;
};

/** `[start, start+duration)` overlaps `[other, other+duration)` on the same day. */
const slotsOverlap = (start, duration, otherStart, otherDuration) =>
  start < otherStart + otherDuration && otherStart < start + duration;

/**
 * Slots are compared as UTC instants, the same convention GET /slots uses for
 * its `isPast` flag (`new Date(`${date}T${time}:00Z`)`).
 */
const hasStarted = (booking, now = new Date()) =>
  new Date(`${booking.date}T${booking.time}:00Z`).getTime() < now.getTime();

const TERMINAL_STATUSES = ['cancelled', 'completed', 'no-show'];

/** Money already collected for the booking — the amount a cancellation owes back. */
const collectedAmount = (booking) => {
  if (booking.paymentStatus === 'paid') return Number(booking.totalAmount) || 0;
  if (booking.paymentStatus === 'deposit_paid') return Number(booking.depositAmount) || 0;
  return 0;
};

/**
 * Cancellation guard shared by PATCH /:id/status and DELETE /:id.
 *
 * A cancelled booking with a collected deposit used to keep `deposit_paid`
 * forever, so the money left no trail. The ledger now flips to `refunded` and
 * the caller gets the amount back in the response; the provider refund itself
 * is manual because booking deposits are not captured through a gateway
 * reference (there is no transaction id on this table to refund against).
 * Patients cannot cancel after the appointment has started — that is a
 * clinic-side bookkeeping action.
 */
const cancellationUpdates = (booking, req, reason) => {
  if (TERMINAL_STATUSES.includes(booking.status)) {
    throw Object.assign(new Error(`Cannot cancel a ${booking.status} booking`), { statusCode: 400 });
  }
  if (req.user.role !== 'admin' && hasStarted(booking)) {
    throw Object.assign(
      new Error('Cannot cancel a booking whose appointment has already passed'),
      { statusCode: 400 },
    );
  }

  const refundDue = collectedAmount(booking);
  const updates = {
    status: 'cancelled',
    cancelledAt: new Date(),
    cancellationReason: reason,
  };
  if (refundDue > 0) updates.paymentStatus = 'refunded';
  return { updates, refundDue };
};

/**
 * GET /api/bookings/doctors — list active doctors
 */
router.get('/doctors', async (req, res, next) => {
  try {
    const doctors = await Doctor.findAll({
      where: { isActive: true },
      attributes: { exclude: ['org_id'] },
      order: [['rating', 'DESC']],
    });
    res.json({ success: true, count: doctors.length, data: doctors });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/bookings/doctors/:slug — single doctor
 */
router.get('/doctors/:slug', async (req, res, next) => {
  try {
    const doctor = await Doctor.findOne({ where: { slug: req.params.slug, isActive: true } });
    if (!doctor) return res.status(404).json({ success: false, error: 'Doctor not found' });
    res.json({ success: true, data: doctor });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/bookings/slots — available time slots for a doctor on a date
 */router.get('/slots', async (req, res, next) => {
  try {
    const { doctorId, date } = req.query;
    if (!doctorId || !date) {
      return res.status(400).json({ success: false, error: 'doctorId and date are required' });
    }

    const doctor = await Doctor.findByPk(parseInt(doctorId, 10));
    if (!doctor) return res.status(404).json({ success: false, error: 'Doctor not found' });

    const dayOfWeek = new Date(date + 'T12:00:00Z').toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase();
    const hours = doctor.workingHours?.[dayOfWeek];
    if (!hours || !hours.start || !hours.end) {
      return res.json({ success: true, data: [], message: 'Doctor not available on this day' });
    }

    const existingBookings = await Booking.findAll({
      where: {
        doctor_id: doctor.id,
        date,
        status: { [Op.notIn]: ['cancelled', 'no-show'] },
      },
      attributes: ['time', 'duration'],
    });

    const bookedSlots = new Set();
    for (const b of existingBookings) {
      const [h, m] = b.time.split(':').map(Number);
      const slotMinutes = h * 60 + m;
      for (let i = 0; i < (b.duration || 30); i += doctor.slotDuration || 30) {
        bookedSlots.add(slotMinutes + i);
      }
    }

    const [startH, startM] = hours.start.split(':').map(Number);
    const [endH, endM] = hours.end.split(':').map(Number);
    const slotDuration = doctor.slotDuration || 30;
    const slots = [];

    for (let min = startH * 60 + startM; min < endH * 60 + endM; min += slotDuration) {
      const h = String(Math.floor(min / 60)).padStart(2, '0');
      const m = String(min % 60).padStart(2, '0');
      const timeStr = `${h}:${m}`;
      const isBooked = bookedSlots.has(min);
      const isPast =
        new Date(`${date}T${timeStr}:00Z`) < new Date();
      slots.push({ time: timeStr, available: !isBooked && !isPast });
    }

    res.json({ success: true, data: slots });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/bookings/services — list active services
 */
router.get('/services', async (req, res, next) => {
  try {
    const services = await Service.findAll({ where: { isActive: true }, order: [['name', 'ASC']] });
    res.json({ success: true, count: services.length, data: services });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /api/bookings — create booking (authenticated, ACID transaction)
 */
router.post('/', protect, async (req, res, next) => {
  try {
    const {
      doctorId, serviceId, date, time, duration = 30,
      reason, notes = '', patientInfo,
    } = req.body;

    if (!doctorId || !date || !time || !reason || !patientInfo) {
      return res.status(400).json({ success: false, error: 'doctorId, date, time, reason, and patientInfo are required' });
    }

    const startMinutes = timeToMinutes(time);
    if (!isValidDate(date) || startMinutes === null) {
      return res.status(400).json({
        success: false,
        error: 'date must be a real YYYY-MM-DD date and time must be HH:MM',
      });
    }

    const durationMinutes = Number(duration);
    if (!Number.isInteger(durationMinutes) || durationMinutes < 1 || durationMinutes > 480) {
      return res.status(400).json({
        success: false,
        error: 'duration must be a whole number of minutes between 1 and 480',
      });
    }

    const doctor = await Doctor.findByPk(parseInt(doctorId, 10));
    if (!doctor) return res.status(404).json({ success: false, error: 'Doctor not found' });

    const service = serviceId ? await Service.findByPk(parseInt(serviceId, 10)) : null;
    const totalAmount = service ? parseFloat(service.price) : parseFloat(doctor.consultationFee);
    const depositAmount = service
      ? parseFloat(service.depositRequired || 0)
      : parseFloat(doctor.depositRequired || 0);

    const booking = await sequelize.transaction(async (t) => {
      // Range-aware conflict probe. Comparing only the start `time` accepted an
      // appointment that overlaps an in-progress one (09:30 into a 09:00-10:00
      // booking) even though GET /slots marks every minute of the range busy.
      const sameDay = await Booking.findAll({
        where: {
          doctor_id: doctor.id,
          date,
          status: { [Op.notIn]: ['cancelled', 'no-show'] },
        },
        transaction: t,
      });
      const clash = sameDay.find((row) => {
        const rowStart = timeToMinutes(row.time);
        if (rowStart === null) return false;
        return slotsOverlap(startMinutes, durationMinutes, rowStart, Number(row.duration) || 30);
      });
      if (clash) {
        throw Object.assign(new Error('This time slot is already booked'), { statusCode: 409 });
      }

      const newBooking = await Booking.create({
        user_id: req.user.id,
        doctor_id: doctor.id,
        service_id: serviceId || null,
        date,
        time,
        duration: durationMinutes,
        reason,
        notes,
        patientInfo,
        totalAmount,
        depositAmount,
        // A deposit at booking time is DUE, not collected — `deposit_paid` is
        // written by the payment path once money actually arrives.
        paymentStatus: 'pending',
      }, { transaction: t });

      return newBooking;
    });

    enqueue(QUEUES.EMAIL, {
      to: req.user.email,
      subject: `Booking Confirmed — ${booking.bookingNumber}`,
      html: `<h2>Booking Confirmed</h2>
        <p>Dear ${patientInfo.firstName},</p>
        <p>Your appointment with <strong>Dr. ${doctor.name}</strong> has been booked.</p>
        <p><strong>Date:</strong> ${date}<br/>
        <strong>Time:</strong> ${time}<br/>
        <strong>Booking #:</strong> ${booking.bookingNumber}</p>
        ${depositAmount > 0 ? `<p><strong>Deposit Required:</strong> $${parseFloat(depositAmount).toFixed(2)}</p>` : ''}
        <p>We will confirm your appointment shortly.</p>`,
    });

    logger.info(`Booking created: ${booking.bookingNumber} by ${req.user.email}`);
    return res.status(201).json({ success: true, data: booking });
  } catch (error) {
    if (error.statusCode) return res.status(error.statusCode).json({ success: false, error: error.message });
    next(error);
  }
});

/**
 * GET /api/bookings — list bookings (user sees own, admin sees all)
 */
router.get('/', protect, async (req, res, next) => {
  try {
    const page = parseInt(req.query.page, 10) || 1;
    const limit = parseInt(req.query.limit, 10) || 10;
    const offset = (page - 1) * limit;
    const { status, doctorId, date, dateFrom, dateTo } = req.query;

    const where = {};
    if (req.user.role !== 'admin') where.user_id = req.user.id;
    if (status) where.status = status;
    if (doctorId) where.doctor_id = parseInt(doctorId, 10);
    if (date) where.date = date;
    if (dateFrom || dateTo) {
      where.date = {};
      if (dateFrom) where.date[Op.gte] = dateFrom;
      if (dateTo) where.date[Op.lte] = dateTo;
    }

    const { count: total, rows: bookings } = await Booking.findAndCountAll({
      where,
      include: [
        { model: Doctor, as: 'doctor', attributes: ['id', 'name', 'specialty', 'avatar'] },
        { model: User, as: 'user', attributes: ['id', 'name', 'email'] },
      ],
      order: [['date', 'DESC'], ['time', 'ASC']],
      limit,
      offset,
    });

    res.json({
      success: true,
      count: bookings.length,
      total,
      pagination: { page, limit, pages: Math.ceil(total / limit) },
      data: bookings,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/bookings/:id — single booking
 */
router.get('/:id', protect, async (req, res, next) => {
  try {
    const booking = await Booking.findByPk(req.params.id, {
      include: [
        { model: Doctor, as: 'doctor' },
        { model: Service, as: 'service' },
        { model: User, as: 'user', attributes: ['id', 'name', 'email', 'phone'] },
      ],
    });
    if (!booking) return res.status(404).json({ success: false, error: 'Booking not found' });
    if (req.user.role !== 'admin' && booking.user_id !== req.user.id) {
      return res.status(403).json({ success: false, error: 'Not authorized' });
    }
    res.json({ success: true, data: booking });
  } catch (error) {
    next(error);
  }
});

/**
 * PATCH /api/bookings/:id/status — update booking status
 */
router.patch('/:id/status', protect, async (req, res, next) => {
  try {
    const { status, notes } = req.body;
    const validStatuses = ['confirmed', 'cancelled', 'completed', 'no-show'];
    if (!validStatuses.includes(status)) {
      return res.status(400).json({ success: false, error: 'Invalid status' });
    }

    const booking = await Booking.findByPk(req.params.id);
    if (!booking) return res.status(404).json({ success: false, error: 'Booking not found' });

    if (req.user.role !== 'admin' && booking.user_id !== req.user.id) {
      return res.status(403).json({ success: false, error: 'Not authorized' });
    }

    // Patients may confirm or cancel their own booking. `completed` and
    // `no-show` are clinic-side outcomes, and a terminal booking cannot be
    // reopened by the patient (no un-cancel).
    if (req.user.role !== 'admin' && !['confirmed', 'cancelled'].includes(status)) {
      return res.status(403).json({
        success: false,
        error: 'Only clinic staff can mark a booking completed or no-show',
      });
    }
    if (req.user.role !== 'admin' && TERMINAL_STATUSES.includes(booking.status)) {
      return res.status(400).json({
        success: false,
        error: `Cannot change a ${booking.status} booking`,
      });
    }

    let updates = { status };
    let refundDue = 0;
    if (status === 'cancelled') {
      ({ updates, refundDue } = cancellationUpdates(booking, req, notes || 'Cancelled by user'));
    } else if (notes) {
      updates.notes = notes;
    }

    if (status === 'confirmed' && ['cancelled', 'no-show'].includes(booking.status)) {
      updates.cancelledAt = null;
      updates.cancellationReason = null;
    }

    await booking.update(updates);

    const doctor = await Doctor.findByPk(booking.doctor_id);
    const refundLine = refundDue > 0
      ? `<p><strong>Refund due:</strong> $${refundDue.toFixed(2)}</p>`
      : '';
    enqueue(QUEUES.EMAIL, {
      to: req.user.email,
      subject: `Booking ${status.charAt(0).toUpperCase() + status.slice(1)} — ${booking.bookingNumber}`,
      html: `<p>Your booking <strong>${booking.bookingNumber}</strong> with Dr. ${doctor?.name || 'N/A'} has been <strong>${status}</strong>.</p>${refundLine}`,
    });

    const body = { success: true, data: booking };
    if (refundDue > 0) body.refundDue = refundDue;
    res.json(body);
  } catch (error) {
    if (error.statusCode) return res.status(error.statusCode).json({ success: false, error: error.message });
    next(error);
  }
});

/**
 * DELETE /api/bookings/:id — cancel booking
 */
router.delete('/:id', protect, async (req, res, next) => {
  try {
    const booking = await Booking.findByPk(req.params.id);
    if (!booking) return res.status(404).json({ success: false, error: 'Booking not found' });

    if (req.user.role !== 'admin' && booking.user_id !== req.user.id) {
      return res.status(403).json({ success: false, error: 'Not authorized' });
    }

    const { updates, refundDue } = cancellationUpdates(
      booking,
      req,
      req.body.reason || 'Cancelled',
    );

    await booking.update(updates);

    const body = { success: true, message: 'Booking cancelled successfully' };
    if (refundDue > 0) body.refundDue = refundDue;
    res.json(body);
  } catch (error) {
    if (error.statusCode) return res.status(error.statusCode).json({ success: false, error: error.message });
    next(error);
  }
});

export default router;
