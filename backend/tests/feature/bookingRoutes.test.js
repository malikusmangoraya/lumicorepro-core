/**
 * Feature tests — routes/booking.routes.js
 *
 * Covers the slot generator (working hours, per-doctor slot length, booked
 * minutes spread over a booking's duration, cancelled/no-show exclusion), the
 * transactional create path (conflict check + pricing from the DB rows), the
 * tenant/owner filters that reach every list & detail query, and the two
 * cancel paths (PATCH status, DELETE) including their windows.
 *
 * Models are the in-memory doubles from tests/helpers/sequelizeFakes.js;
 * `sequelize.transaction` is the fake from createFakeSequelize(); the queue and
 * logger are stubbed so the email payloads can be asserted.
 */
import express from 'express';
import request from 'supertest';
import { Op } from 'sequelize';
import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { createFakeModel, createFakeSequelize } from '../helpers/sequelizeFakes.js';

const BUYER = { id: 10, role: 'user', email: 'buyer@example.com' };
const ADMIN = { id: 99, role: 'admin', email: 'admin@example.com' };

let currentUser = { ...BUYER };

/** A weekday far enough in the future that no generated slot is "past". */
const DATE = new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10);
const OFF_DATE = new Date(Date.now() + 31 * 86400000).toISOString().slice(0, 10);
const PAST_DATE = '2020-01-06';
const weekdayOf = (isoDate) =>
  new Date(`${isoDate}T12:00:00Z`).toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase();
const DAY = weekdayOf(DATE);
const OFF_DAY = weekdayOf(OFF_DATE);
const ALL_DAYS = [
  'monday',
  'tuesday',
  'wednesday',
  'thursday',
  'friday',
  'saturday',
  'sunday',
].reduce((acc, d) => ({ ...acc, [d]: { start: '09:00', end: '12:00' } }), {});

/**
 * Poison switch for the error paths: jest.config.js resets mock implementations
 * between tests, and these models are plain objects, so a hand-rolled failure
 * flag is the only way to make one call reject without breaking later tests.
 */
let forcedFailure = null;

const mockLogger = {
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
  debug: jest.fn(),
};

jest.unstable_mockModule('../../utils/logger.js', () => ({
  __esModule: true,
  default: mockLogger,
  withRequestId: () => mockLogger,
  redact: (value) => value,
}));

jest.unstable_mockModule('../../middleware/auth.js', () => ({
  __esModule: true,
  protect: (req, _res, next) => {
    req.user = { ...currentUser };
    next();
  },
  authorize: (...roles) => (req, res, next) => {
    if (!req.user || !roles.includes(req.user.role)) {
      return res.status(403).json({ success: false, error: 'Not authorized' });
    }
    return next();
  },
  optionalProtect: (req, _res, next) => next(),
}));

const QUEUES = { EMAIL: 'lh-email', CART_RECOVERY: 'lh-cart-recovery' };
const enqueue = jest.fn();
jest.unstable_mockModule('../../services/queue/queue.service.js', () => ({
  __esModule: true,
  QUEUES,
  enqueue,
  getQueue: jest.fn(),
  default: { QUEUES, enqueue },
}));

const fakeDb = createFakeSequelize();
jest.unstable_mockModule('../../config/database.js', () => ({
  __esModule: true,
  sequelize: fakeDb,
  default: fakeDb,
  connectDB: async () => true,
}));

const doctorRows = () => [
  {
    id: 1,
    name: 'Ada Nex',
    slug: 'ada-nex',
    specialty: 'Neurology',
    avatar: 'ada.png',
    rating: '4.80',
    consultationFee: '120.00',
    depositRequired: '30.00',
    slotDuration: 30,
    isActive: true,
    org_id: 3,
    workingHours: { ...ALL_DAYS, [OFF_DAY]: null },
  },
  {
    id: 2,
    name: 'Bob Late',
    slug: 'bob-late',
    specialty: 'Cardiology',
    avatar: '',
    rating: '3.10',
    consultationFee: '90.00',
    depositRequired: '0.00',
    slotDuration: 30,
    isActive: false,
    org_id: null,
    workingHours: { [DAY]: { start: '09:00', end: '12:00' } },
  },
  {
    id: 3,
    name: 'Cy Hour',
    slug: 'cy-hour',
    specialty: 'Dermatology',
    avatar: '',
    rating: '5.00',
    consultationFee: '80.00',
    depositRequired: '0.00',
    slotDuration: 60,
    isActive: true,
    org_id: null,
    workingHours: { ...ALL_DAYS, [OFF_DAY]: { start: '10:00', end: '11:00' } },
  },
  {
    id: 4,
    name: 'De Closed',
    slug: 'de-closed',
    specialty: 'ENT',
    avatar: '',
    rating: '4.00',
    consultationFee: '50.00',
    depositRequired: '0.00',
    slotDuration: 30,
    isActive: true,
    org_id: null,
    workingHours: { ...ALL_DAYS, [DAY]: { start: null, end: '12:00' } },
  },
];

const serviceRows = () => [
  { id: 5, name: 'Consultation', price: '200.00', depositRequired: '50.00', duration: 45, isActive: true },
  { id: 6, name: 'Legacy Package', price: '10.00', depositRequired: '0.00', duration: 15, isActive: false },
];

const userRows = () => [
  { id: 10, name: 'Ann Book', email: 'buyer@example.com', phone: '+15550001' },
  { id: 20, name: 'Bo Other', email: 'other@example.com', phone: '' },
];

const bookingRows = () => [
  {
    id: 1,
    user_id: 10,
    doctor_id: 1,
    service_id: null,
    bookingNumber: 'BK-TEST-1',
    date: DATE,
    time: '09:00',
    duration: 60,
    status: 'pending',
    reason: 'Migraine follow-up',
    notes: '',
    patientInfo: { firstName: 'Ann', lastName: 'Book' },
    paymentStatus: 'deposit_paid',
    depositAmount: '30.00',
    totalAmount: '120.00',
    cancelledAt: null,
    cancellationReason: null,
  },
  {
    id: 2,
    user_id: 20,
    doctor_id: 1,
    service_id: 5,
    bookingNumber: 'BK-TEST-2',
    date: DATE,
    time: '11:00',
    duration: 30,
    status: 'confirmed',
    reason: 'Rash',
    notes: '',
    patientInfo: { firstName: 'Bo' },
    paymentStatus: 'paid',
    depositAmount: '50.00',
    totalAmount: '200.00',
    cancelledAt: null,
    cancellationReason: null,
  },
  {
    id: 3,
    user_id: 10,
    doctor_id: 1,
    service_id: null,
    bookingNumber: 'BK-TEST-3',
    date: DATE,
    time: '10:00',
    duration: 30,
    status: 'cancelled',
    reason: 'Cancelled trip',
    notes: 'left',
    patientInfo: { firstName: 'Ann' },
    paymentStatus: 'refunded',
    depositAmount: '0.00',
    totalAmount: '120.00',
    cancelledAt: new Date('2026-01-05T00:00:00Z'),
    cancellationReason: 'Changed plans',
  },
  {
    id: 4,
    user_id: 10,
    doctor_id: 1,
    service_id: null,
    bookingNumber: 'BK-TEST-4',
    date: PAST_DATE,
    time: '09:30',
    duration: 30,
    status: 'completed',
    reason: 'Annual review',
    notes: '',
    patientInfo: { firstName: 'Ann' },
    paymentStatus: 'paid',
    depositAmount: '0.00',
    totalAmount: '120.00',
    cancelledAt: null,
    cancellationReason: null,
  },
  {
    id: 5,
    user_id: 10,
    doctor_id: 999,
    service_id: null,
    bookingNumber: 'BK-TEST-5',
    date: DATE,
    time: '11:30',
    duration: 30,
    status: 'pending',
    reason: 'No doctor row',
    notes: '',
    patientInfo: { firstName: 'Ann' },
    paymentStatus: 'pending',
    depositAmount: '0.00',
    totalAmount: '0.00',
    cancelledAt: null,
    cancellationReason: null,
  },
];

const Booking = createFakeModel('Booking', bookingRows());
const Doctor = createFakeModel('Doctor', doctorRows());
const Service = createFakeModel('Service', serviceRows());
const User = createFakeModel('User', userRows());

/** The real Booking model generates `bookingNumber` in a beforeCreate hook. */
let bookingSeq = 100;
const baseBookingCreate = Booking.create;
Booking.create = async (values = {}, options = {}) =>
  baseBookingCreate(
    { ...values, bookingNumber: values.bookingNumber || `BK-TEST-${(bookingSeq += 1)}` },
    options,
  );

/** Route the listed calls through the `forcedFailure` poison switch. */
const poisable = (model, method) => {
  const original = model[method];
  model[method] = async (...args) => {
    if (forcedFailure && forcedFailure.target === `${model.name}.${method}`) {
      throw new Error(forcedFailure.message);
    }
    return original(...args);
  };
};
poisable(Doctor, 'findAll');
poisable(Booking, 'findAll');
poisable(Booking, 'create');

jest.unstable_mockModule('../../models/Booking.js', () => ({ __esModule: true, default: Booking }));
jest.unstable_mockModule('../../models/Doctor.js', () => ({ __esModule: true, default: Doctor }));
jest.unstable_mockModule('../../models/Service.js', () => ({ __esModule: true, default: Service }));
jest.unstable_mockModule('../../models/User.js', () => ({ __esModule: true, default: User }));

const { default: bookingRoutes } = await import('../../routes/booking.routes.js');

const app = express();
app.use(express.json());
app.use('/api/bookings', bookingRoutes);
app.use((err, _req, res, _next) => {
  res.status(err.statusCode || 500).json({ success: false, error: err.message });
});

const callsOf = (model, method) =>
  model.calls.filter((c) => c.method === method).map((c) => c.options);
const bookingRow = (id) => Booking.rows.find((r) => r.id === id);
const slotTimes = (body) => body.data.map((s) => `${s.time}=${s.available ? 'open' : 'taken'}`);

beforeEach(() => {
  Booking.rows.length = 0;
  Booking.rows.push(...bookingRows());
  Booking.calls.length = 0;
  Doctor.rows.length = 0;
  Doctor.rows.push(...doctorRows());
  Doctor.calls.length = 0;
  Service.rows.length = 0;
  Service.rows.push(...serviceRows());
  Service.calls.length = 0;
  User.calls.length = 0;
  currentUser = { ...BUYER };
  forcedFailure = null;
  enqueue.mockResolvedValue({ jobId: 'job-1' });
});

describe('GET /api/bookings/doctors', () => {
  it('lists only active doctors, best rated first', async () => {
    const res = await request(app).get('/api/bookings/doctors');

    expect(res.status).toBe(200);
    const [query] = callsOf(Doctor, 'findAll');
    expect(query.where).toEqual({ isActive: true });
    expect(query.order).toEqual([['rating', 'DESC']]);
    expect(res.body.success).toBe(true);
    expect(res.body.count).toBe(3);
    expect(res.body.data.map((d) => d.id)).toEqual([1, 3, 4]);
  });

  it('asks that the org column be projected away', async () => {
    const res = await request(app).get('/api/bookings/doctors');

    const [query] = callsOf(Doctor, 'findAll');
    expect(query.attributes).toEqual({ exclude: ['org_id'] });
    expect(res.body.success).toBe(true);
  });

  it('hands a database failure to the error handler', async () => {
    forcedFailure = { target: 'Doctor.findAll', message: 'connection reset' };

    const res = await request(app).get('/api/bookings/doctors');

    expect(res.status).toBe(500);
    expect(res.body).toEqual({ success: false, error: 'connection reset' });
  });
});

describe('GET /api/bookings/doctors/:slug', () => {
  it('finds an active doctor by slug', async () => {
    const res = await request(app).get('/api/bookings/doctors/ada-nex');

    expect(res.status).toBe(200);
    expect(callsOf(Doctor, 'findOne')[0].where).toEqual({ slug: 'ada-nex', isActive: true });
    expect(res.body.data.name).toBe('Ada Nex');
  });

  it('404s for an inactive doctor', async () => {
    const res = await request(app).get('/api/bookings/doctors/bob-late');

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Doctor not found' });
  });

  it('404s for an unknown slug', async () => {
    const res = await request(app).get('/api/bookings/doctors/nope');

    expect(res.status).toBe(404);
  });
});

describe('GET /api/bookings/slots', () => {
  it('400s without doctorId or date', async () => {
    const noDate = await request(app).get('/api/bookings/slots?doctorId=1');
    const noDoctor = await request(app).get('/api/bookings/slots?date=' + DATE);

    expect(noDate.status).toBe(400);
    expect(noDoctor.status).toBe(400);
    expect(noDate.body).toEqual({ success: false, error: 'doctorId and date are required' });
    expect(callsOf(Booking, 'findAll')).toHaveLength(0);
  });

  it('404s for an unknown doctor', async () => {
    const res = await request(app).get(`/api/bookings/slots?doctorId=777&date=${DATE}`);

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Doctor not found' });
  });

  it('says so when the doctor does not work that day', async () => {
    const res = await request(app).get(`/api/bookings/slots?doctorId=1&date=${OFF_DATE}`);

    expect(res.status).toBe(200);
    expect(res.body).toEqual({
      success: true,
      data: [],
      message: 'Doctor not available on this day',
    });
    expect(callsOf(Booking, 'findAll')).toHaveLength(0);
  });

  it('says so when the schedule row has no start time', async () => {
    const res = await request(app).get(`/api/bookings/slots?doctorId=4&date=${DATE}`);

    expect(res.body.message).toBe('Doctor not available on this day');
  });

  it('generates the working window and marks booked minutes unavailable', async () => {
    const res = await request(app).get(`/api/bookings/slots?doctorId=1&date=${DATE}`);

    expect(res.status).toBe(200);
    expect(slotTimes(res.body)).toEqual([
      '09:00=taken',
      '09:30=taken',
      '10:00=open',
      '10:30=open',
      '11:00=taken',
      '11:30=open',
    ]);
  });

  it('excludes cancelled and no-show bookings from the busy set', async () => {
    await request(app).get(`/api/bookings/slots?doctorId=1&date=${DATE}`);

    const [query] = callsOf(Booking, 'findAll');
    expect(query.where).toEqual({
      doctor_id: 1,
      date: DATE,
      status: { [Op.notIn]: ['cancelled', 'no-show'] },
    });
    expect(query.attributes).toEqual(['time', 'duration']);
    // BK-TEST-3 is a cancelled 10:00 booking, so 10:00 stays open.
  });

  it('walks the day in the doctor own slot length', async () => {
    const res = await request(app).get(`/api/bookings/slots?doctorId=3&date=${DATE}`);

    expect(res.body.data.map((s) => s.time)).toEqual(['09:00', '10:00', '11:00']);
  });

  it('marks a past day as fully unavailable', async () => {
    const res = await request(app).get(`/api/bookings/slots?doctorId=3&date=${PAST_DATE}`);

    expect(res.status).toBe(200);
    expect(res.body.data.length).toBeGreaterThan(0);
    expect(res.body.data.every((s) => s.available === false)).toBe(true);
  });

  it('hands a database failure to the error handler', async () => {
    forcedFailure = { target: 'Booking.findAll', message: 'slot read failed' };

    const res = await request(app).get(`/api/bookings/slots?doctorId=1&date=${DATE}`);

    expect(res.status).toBe(500);
    expect(res.body).toEqual({ success: false, error: 'slot read failed' });
  });
});

describe('GET /api/bookings/services', () => {
  it('lists active services alphabetically', async () => {
    const res = await request(app).get('/api/bookings/services');

    expect(res.status).toBe(200);
    const [query] = callsOf(Service, 'findAll');
    expect(query.where).toEqual({ isActive: true });
    expect(query.order).toEqual([['name', 'ASC']]);
    expect(res.body.count).toBe(1);
    expect(res.body.data[0].name).toBe('Consultation');
  });
});

describe('POST /api/bookings', () => {
  const validBody = (overrides = {}) => ({
    doctorId: 1,
    date: DATE,
    time: '10:30',
    reason: 'Consultation',
    patientInfo: { firstName: 'Ann', lastName: 'Book' },
    ...overrides,
  });

  it('400s when a required field is missing', async () => {
    const noReason = await request(app).post('/api/bookings').send(validBody({ reason: '' }));
    const noPatient = await request(app).post('/api/bookings').send({ doctorId: 1, date: DATE, time: '10:30' });

    expect(noReason.status).toBe(400);
    expect(noPatient.status).toBe(400);
    expect(noPatient.body).toEqual({
      success: false,
      error: 'doctorId, date, time, reason, and patientInfo are required',
    });
    expect(callsOf(Booking, 'create')).toHaveLength(0);
  });

  it('404s for an unknown doctor and books nothing', async () => {
    const res = await request(app).post('/api/bookings').send(validBody({ doctorId: 777 }));

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Doctor not found' });
    expect(callsOf(Booking, 'create')).toHaveLength(0);
  });

  it('409s when the exact slot is already held', async () => {
    const res = await request(app).post('/api/bookings').send(validBody({ time: '09:00' }));

    expect(res.status).toBe(409);
    expect(res.body).toEqual({ success: false, error: 'This time slot is already booked' });
    expect(callsOf(Booking, 'create')).toHaveLength(0);
    const [conflictQuery] = callsOf(Booking, 'findAll');
    expect(conflictQuery.transaction).toBe(fakeDb._transaction);
    // Range probe: every live booking for the doctor/day comes back and the
    // overlap is decided in JS, so no `time` equality is pushed to SQL.
    expect(conflictQuery.where).toEqual({
      doctor_id: 1,
      date: DATE,
      status: { [Op.notIn]: ['cancelled', 'no-show'] },
    });
  });

  it('ignores cancelled bookings when checking the slot', async () => {
    const res = await request(app).post('/api/bookings').send(validBody({ time: '10:00' }));

    expect(res.status).toBe(201);
    expect(bookingRow(res.body.data.id).time).toBe('10:00');
  });

  it('prices from the service row inside the transaction', async () => {
    const res = await request(app)
      .post('/api/bookings')
      .send(validBody({ serviceId: 5, duration: 45, time: '14:00' }));

    expect(res.status).toBe(201);
    const [created] = callsOf(Booking, 'create');
    expect(created.options.transaction).toBe(fakeDb._transaction);
    expect(created.values).toEqual(
      expect.objectContaining({
        user_id: BUYER.id,
        doctor_id: 1,
        service_id: 5,
        date: DATE,
        time: '14:00',
        duration: 45,
        reason: 'Consultation',
        notes: '',
        patientInfo: { firstName: 'Ann', lastName: 'Book' },
        totalAmount: 200,
        depositAmount: 50,
        paymentStatus: 'pending',
      }),
    );
    expect(res.body.data.bookingNumber).toMatch(/^BK-TEST-/);
  });

  it('falls back to the doctor fee when no service is chosen', async () => {
    const res = await request(app).post('/api/bookings').send(validBody());

    expect(res.status).toBe(201);
    const { values } = callsOf(Booking, 'create')[0];
    expect(values.totalAmount).toBe(120);
    expect(values.depositAmount).toBe(30);
    expect(values.service_id).toBeNull();
  });

  it('defaults the duration to 30 minutes', async () => {
    await request(app).post('/api/bookings').send(validBody());

    expect(callsOf(Booking, 'create')[0].values.duration).toBe(30);
  });

  it('queues the confirmation email with the deposit line', async () => {
    const res = await request(app)
      .post('/api/bookings')
      .send(validBody({ serviceId: 5 }));

    expect(enqueue).toHaveBeenCalledTimes(1);
    const [queueName, job] = enqueue.mock.calls[0];
    expect(queueName).toBe(QUEUES.EMAIL);
    expect(job.to).toBe(BUYER.email);
    expect(job.subject).toBe(`Booking Confirmed — ${res.body.data.bookingNumber}`);
    expect(job.html).toContain('Dr. Ada Nex');
    expect(job.html).toContain('Ann');
    expect(job.html).toContain('Deposit Required:</strong> $50.00');
    expect(mockLogger.info).toHaveBeenCalledWith(
      expect.stringContaining(`Booking created: ${res.body.data.bookingNumber}`),
    );
  });

  it('omits the deposit line when nothing is due', async () => {
    await request(app).post('/api/bookings').send(validBody({ doctorId: 3 }));

    expect(enqueue.mock.calls[0][1].html).not.toContain('Deposit Required');
  });

  it('500s when the booking insert fails', async () => {
    forcedFailure = { target: 'Booking.create', message: 'insert failed' };

    const res = await request(app).post('/api/bookings').send(validBody());

    expect(res.status).toBe(500);
    expect(res.body).toEqual({ success: false, error: 'insert failed' });
    expect(enqueue).not.toHaveBeenCalled();
  });

  /**
   * FIXED — the conflict probe compared only the start `time` while GET /slots
   * marks every minute of a booking's duration busy. The probe now loads the
   * day's live bookings and checks the ranges, so a booking that overlaps an
   * in-progress appointment is refused.
   */
  it('refuses a slot that overlaps an in-progress appointment', async () => {
    const overlap = await request(app).post('/api/bookings').send(validBody({ time: '09:30' }));

    expect(overlap.status).toBe(409);
    expect(overlap.body).toEqual({ success: false, error: 'This time slot is already booked' });
    expect(callsOf(Booking, 'create')).toHaveLength(0);
    const [conflictQuery] = callsOf(Booking, 'findAll');
    expect(conflictQuery.where).toEqual({
      doctor_id: 1,
      date: DATE,
      status: { [Op.notIn]: ['cancelled', 'no-show'] },
    });
  });

  it('allows a booking that starts when the previous one ends', async () => {
    // BK-TEST-1 is 09:00 + 60 minutes, so 10:00 is the first free minute —
    // except BK-TEST-3 sits at 10:00 and is cancelled, which must not count.
    const res = await request(app).post('/api/bookings').send(validBody({ time: '10:00' }));

    expect(res.status).toBe(201);
  });

  it.each([
    ['a malformed date', { date: '2026-02-30' }],
    ['a malformed time', { time: '9am' }],
    ['a zero duration', { duration: 0 }],
    ['a 9-hour appointment', { duration: 540 }],
    ['a fractional duration', { duration: 12.5 }],
  ])('rejects %s with 400 before the transaction', async (_label, override) => {
    const res = await request(app).post('/api/bookings').send(validBody(override));

    expect(res.status).toBe(400);
    expect(callsOf(Booking, 'create')).toHaveLength(0);
  });

  /**
   * FIXED — `depositAmount > 0 ? 'pending' : 'pending'` was a dead branch. A
   * deposit at booking time is money DUE, not collected: the amount is recorded
   * and the status stays `pending` until the payment path captures it.
   */
  it('records a deposit as due without claiming it was paid', async () => {
    const withDeposit = await request(app)
      .post('/api/bookings')
      .send(validBody({ serviceId: 5 }));
    const [created] = callsOf(Booking, 'create');

    expect(withDeposit.status).toBe(201);
    expect(created.values.depositAmount).toBe(50);
    expect(created.values.paymentStatus).toBe('pending');
  });
});

describe('GET /api/bookings', () => {
  it('pins a non-admin listing to the caller', async () => {
    const res = await request(app).get('/api/bookings');

    expect(res.status).toBe(200);
    const [query] = callsOf(Booking, 'findAndCountAll');
    expect(query.where).toEqual({ user_id: BUYER.id });
    expect(query.include.map((i) => i.as)).toEqual(['doctor', 'user']);
    expect(query.order).toEqual([['date', 'DESC'], ['time', 'ASC']]);
    expect(res.body.success).toBe(true);
    expect(res.body.total).toBe(4);
    expect(res.body.pagination).toEqual({ page: 1, limit: 10, pages: 1 });
  });

  it('lets an admin list every booking', async () => {
    currentUser = { ...ADMIN };

    const res = await request(app).get('/api/bookings');

    expect(callsOf(Booking, 'findAndCountAll')[0].where).toEqual({});
    expect(res.body.total).toBe(5);
  });

  it('filters by status and doctor', async () => {
    const res = await request(app).get('/api/bookings?status=pending&doctorId=1');

    expect(callsOf(Booking, 'findAndCountAll')[0].where).toEqual({
      user_id: BUYER.id,
      status: 'pending',
      doctor_id: 1,
    });
    expect(res.body.data.map((b) => b.id)).toEqual([1]);
  });

  it('filters by a single date', async () => {
    await request(app).get(`/api/bookings?date=${DATE}`);

    expect(callsOf(Booking, 'findAndCountAll')[0].where).toEqual({
      user_id: BUYER.id,
      date: DATE,
    });
  });

  it('builds a range when dateFrom/dateTo are used', async () => {
    await request(app).get(`/api/bookings?dateFrom=${PAST_DATE}&dateTo=${DATE}`);

    const [query] = callsOf(Booking, 'findAndCountAll');
    expect(query.where.date[Op.gte]).toBe(PAST_DATE);
    expect(query.where.date[Op.lte]).toBe(DATE);
  });

  it('a range replaces an exact date filter', async () => {
    await request(app).get(`/api/bookings?date=${DATE}&dateFrom=${PAST_DATE}`);

    const [query] = callsOf(Booking, 'findAndCountAll');
    expect(query.where.date[Op.gte]).toBe(PAST_DATE);
    expect(typeof query.where.date).toBe('object');
  });

  it('pages with the documented defaults', async () => {
    const res = await request(app).get('/api/bookings?page=2&limit=1');

    const [query] = callsOf(Booking, 'findAndCountAll');
    expect(query.limit).toBe(1);
    expect(query.offset).toBe(1);
    expect(res.body.pagination).toEqual({ page: 2, limit: 1, pages: 4 });
    expect(res.body.count).toBe(1);
  });

  it('coerces garbage paging params to the defaults', async () => {
    const res = await request(app).get('/api/bookings?page=abc&limit=zz');

    expect(res.body.pagination).toEqual({ page: 1, limit: 10, pages: 1 });
  });
});

describe('GET /api/bookings/:id', () => {
  it('returns the owner booking with its joins', async () => {
    const res = await request(app).get('/api/bookings/1');

    expect(res.status).toBe(200);
    const [query] = callsOf(Booking, 'findByPk');
    expect(query.include.map((i) => i.as)).toEqual(['doctor', 'service', 'user']);
    expect(query.include[2].attributes).toEqual(['id', 'name', 'email', 'phone']);
    expect(res.body.data.bookingNumber).toBe('BK-TEST-1');
  });

  it('404s for an unknown booking', async () => {
    const res = await request(app).get('/api/bookings/404');

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Booking not found' });
  });

  it('403s when the booking belongs to somebody else', async () => {
    const res = await request(app).get('/api/bookings/2');

    expect(res.status).toBe(403);
    expect(res.body).toEqual({ success: false, error: 'Not authorized' });
  });

  it('lets an admin read another patient booking', async () => {
    currentUser = { ...ADMIN };

    const res = await request(app).get('/api/bookings/2');

    expect(res.status).toBe(200);
    expect(res.body.data.id).toBe(2);
  });
});

describe('PATCH /api/bookings/:id/status', () => {
  it('400s on a status outside the enum', async () => {
    for (const status of ['refunded', '', 'CANCELLED']) {
      const res = await request(app).patch('/api/bookings/1/status').send({ status });
      expect(res.status).toBe(400);
      expect(res.body).toEqual({ success: false, error: 'Invalid status' });
    }
    expect(bookingRow(1).status).toBe('pending');
  });

  it('404s for an unknown booking', async () => {
    const res = await request(app).patch('/api/bookings/404/status').send({ status: 'confirmed' });

    expect(res.status).toBe(404);
  });

  it('403s for another patient booking', async () => {
    const res = await request(app).patch('/api/bookings/2/status').send({ status: 'cancelled' });

    expect(res.status).toBe(403);
    expect(bookingRow(2).status).toBe('confirmed');
    expect(enqueue).not.toHaveBeenCalled();
  });

  it('confirms the booking and notifies by email', async () => {
    const res = await request(app).patch('/api/bookings/1/status').send({ status: 'confirmed' });

    expect(res.status).toBe(200);
    expect(bookingRow(1).status).toBe('confirmed');
    expect(bookingRow(1).cancelledAt).toBeNull();
    expect(enqueue).toHaveBeenCalledWith(
      QUEUES.EMAIL,
      expect.objectContaining({
        to: BUYER.email,
        subject: 'Booking Confirmed — BK-TEST-1',
      }),
    );
    expect(enqueue.mock.calls[0][1].html).toContain('Dr. Ada Nex');
  });

  it('records the note when the status change carries one', async () => {
    const res = await request(app)
      .patch('/api/bookings/1/status')
      .send({ status: 'confirmed', notes: 'Rescheduled by clinic' });

    expect(res.body.data.notes).toBe('Rescheduled by clinic');
    expect(bookingRow(1).notes).toBe('Rescheduled by clinic');
  });

  it('stamps the cancellation fields and the refund ledger', async () => {
    const before = Date.now();
    const res = await request(app)
      .patch('/api/bookings/1/status')
      .send({ status: 'cancelled', notes: 'Patient ill' });

    expect(res.status).toBe(200);
    // BK-TEST-1 holds a $30 deposit, so cancelling must leave a refund trail
    // instead of keeping `deposit_paid` on a dead booking.
    expect(res.body.refundDue).toBe(30);
    const row = bookingRow(1);
    expect(row.status).toBe('cancelled');
    expect(row.paymentStatus).toBe('refunded');
    expect(row.cancellationReason).toBe('Patient ill');
    expect(row.cancelledAt).toBeInstanceOf(Date);
    expect(row.cancelledAt.getTime()).toBeGreaterThanOrEqual(before - 1000);
  });

  it('defaults the cancellation reason when no note is given', async () => {
    await request(app).patch('/api/bookings/1/status').send({ status: 'cancelled' });

    expect(bookingRow(1).cancellationReason).toBe('Cancelled by user');
  });

  it('still writes the email when the doctor row is gone', async () => {
    currentUser = { ...ADMIN };

    const res = await request(app).patch('/api/bookings/5/status').send({ status: 'completed' });

    expect(res.status).toBe(200);
    expect(enqueue.mock.calls[0][1].html).toContain('Dr. N/A');
  });

  /**
   * FIXED — `protect` plus an owner check was the only gate. `completed` and
   * `no-show` are clinic-side outcomes and a terminal booking cannot be
   * reopened by the patient.
   */
  it('refuses to let a patient mark their booking completed', async () => {
    const res = await request(app).patch('/api/bookings/1/status').send({ status: 'completed' });

    expect(res.status).toBe(403);
    expect(res.body).toEqual({
      success: false,
      error: 'Only clinic staff can mark a booking completed or no-show',
    });
    expect(bookingRow(1).status).toBe('pending');
    expect(enqueue).not.toHaveBeenCalled();
  });

  it('refuses to let a patient mark their booking no-show', async () => {
    const res = await request(app).patch('/api/bookings/1/status').send({ status: 'no-show' });

    expect(res.status).toBe(403);
    expect(bookingRow(1).status).toBe('pending');
  });

  it('refuses to let a patient un-cancel a cancelled booking', async () => {
    const res = await request(app).patch('/api/bookings/3/status').send({ status: 'confirmed' });

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: 'Cannot change a cancelled booking' });
    expect(bookingRow(3).status).toBe('cancelled');
  });

  it('lets an admin mark a booking completed', async () => {
    currentUser = { ...ADMIN };

    const res = await request(app).patch('/api/bookings/1/status').send({ status: 'completed' });

    expect(res.status).toBe(200);
    expect(bookingRow(1).status).toBe('completed');
  });

  it('lets an admin reopen a cancelled booking', async () => {
    currentUser = { ...ADMIN };

    const res = await request(app).patch('/api/bookings/3/status').send({ status: 'confirmed' });

    expect(res.status).toBe(200);
    expect(bookingRow(3).status).toBe('confirmed');
  });
});

describe('DELETE /api/bookings/:id', () => {
  it('cancels a live booking and stamps the reason', async () => {
    const res = await request(app).delete('/api/bookings/1').send({ reason: 'Hospitalised' });

    expect(res.status).toBe(200);
    // BK-TEST-1 has a $30 deposit on file, so the cancellation carries the
    // refund amount back to the caller.
    expect(res.body).toEqual({
      success: true,
      message: 'Booking cancelled successfully',
      refundDue: 30,
    });
    const row = bookingRow(1);
    expect(row.status).toBe('cancelled');
    expect(row.paymentStatus).toBe('refunded');
    expect(row.cancellationReason).toBe('Hospitalised');
    expect(row.cancelledAt).toBeInstanceOf(Date);
  });

  it('falls back to a generic cancellation reason', async () => {
    await request(app).delete('/api/bookings/1');

    expect(bookingRow(1).cancellationReason).toBe('Cancelled');
  });

  it('404s for an unknown booking', async () => {
    const res = await request(app).delete('/api/bookings/404');

    expect(res.status).toBe(404);
  });

  it('403s when asked to cancel another patient booking', async () => {
    const res = await request(app).delete('/api/bookings/2');

    expect(res.status).toBe(403);
    expect(bookingRow(2).status).toBe('confirmed');
  });

  it('refuses to cancel an already cancelled booking', async () => {
    const res = await request(app).delete('/api/bookings/3');

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: 'Cannot cancel a cancelled booking' });
    expect(bookingRow(3).status).toBe('cancelled');
  });

  it('refuses to cancel a completed booking', async () => {
    const res = await request(app).delete('/api/bookings/4');

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: 'Cannot cancel a completed booking' });
  });

  it('lets an admin cancel a booking they do not own', async () => {
    currentUser = { ...ADMIN };

    const res = await request(app).delete('/api/bookings/2');

    expect(res.status).toBe(200);
    expect(bookingRow(2).status).toBe('cancelled');
  });

  /**
   * FIXED — there was no cancellation window and no refund leg. A patient now
   * cannot cancel after the appointment has started (that is clinic-side
   * bookkeeping), and an admin cancellation of a collected booking flips the
   * ledger to `refunded` and reports the amount.
   */
  it('refuses a patient cancel of a past-date booking', async () => {
    Booking.rows.push({
      ...bookingRow(1),
      id: 60,
      date: PAST_DATE,
      time: '09:00',
      status: 'pending',
      paymentStatus: 'deposit_paid',
      depositAmount: '30.00',
    });

    const res = await request(app).delete('/api/bookings/60');

    expect(res.status).toBe(400);
    expect(res.body).toEqual({
      success: false,
      error: 'Cannot cancel a booking whose appointment has already passed',
    });
    expect(bookingRow(60).status).toBe('pending');
    expect(bookingRow(60).paymentStatus).toBe('deposit_paid');
  });

  it('lets an admin cancel a past-date booking and records the refund', async () => {
    currentUser = { ...ADMIN };
    Booking.rows.push({
      ...bookingRow(1),
      id: 61,
      date: PAST_DATE,
      time: '09:00',
      status: 'pending',
      paymentStatus: 'deposit_paid',
      depositAmount: '30.00',
    });

    const res = await request(app).delete('/api/bookings/61');

    expect(res.status).toBe(200);
    expect(res.body.refundDue).toBe(30);
    expect(bookingRow(61).status).toBe('cancelled');
    expect(bookingRow(61).paymentStatus).toBe('refunded');
  });

  it('cancels an unpaid booking without inventing a refund', async () => {
    const res = await request(app).delete('/api/bookings/5');

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ success: true, message: 'Booking cancelled successfully' });
    expect(bookingRow(5).paymentStatus).toBe('pending');
  });
});
