import { z } from 'zod';

export const createBookingSchema = z.object({
  body: z.object({
    doctorId: z.number().int().positive('Doctor ID is required'),
    serviceId: z.number().int().positive().optional(),
    date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be YYYY-MM-DD'),
    time: z.string().regex(/^\d{2}:\d{2}$/, 'Time must be HH:MM'),
    duration: z.number().int().min(15).max(480).optional().default(30),
    reason: z.string().min(1, 'Reason for visit is required').max(500),
    notes: z.string().max(1000).optional().default(''),
    patientInfo: z.object({
      firstName: z.string().min(1).max(100),
      lastName: z.string().min(1).max(100),
      dateOfBirth: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
      phone: z.string().min(10).max(20),
      email: z.string().email(),
      insuranceProvider: z.string().max(200).optional(),
      insuranceId: z.string().max(100).optional(),
    }),
  }),
});

export const updateBookingStatusSchema = z.object({
  body: z.object({
    status: z.enum(['confirmed', 'cancelled', 'completed', 'no-show']),
    notes: z.string().max(500).optional(),
  }),
  params: z.object({
    id: z.string().regex(/^\d+$/, 'Booking ID must be a number'),
  }),
});

export const bookingQuerySchema = z.object({
  query: z.object({
    page: z.string().regex(/^\d+$/).optional(),
    limit: z.string().regex(/^\d+$/).optional(),
    status: z.enum(['pending', 'confirmed', 'cancelled', 'completed', 'no-show']).optional(),
    doctorId: z.string().regex(/^\d+$/).optional(),
    date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
    dateFrom: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
    dateTo: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  }),
});

export const availableSlotsSchema = z.object({
  query: z.object({
    doctorId: z.string().regex(/^\d+$/, 'Doctor ID is required'),
    date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be YYYY-MM-DD'),
  }),
});
