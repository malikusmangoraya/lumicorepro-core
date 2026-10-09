import { z } from 'zod';

export const registerSchema = z.object({
  body: z.object({
    name: z.string().trim().min(1, 'Name is required').max(100),
    email: z.string().trim().email('Valid email is required').toLowerCase(),
    password: z.string().min(6, 'Password must be at least 6 characters').max(128),
    role: z.enum(['user', 'vendor']).optional().default('user'),
    captchaToken: z.string().optional(),
  }),
});

export const loginSchema = z.object({
  body: z.object({
    email: z.string().trim().email('Valid email is required').toLowerCase(),
    password: z.string().min(1, 'Password is required'),
    captchaToken: z.string().optional(),
  }),
});

export const forgotPasswordSchema = z.object({
  body: z.object({
    email: z.string().trim().email('Valid email is required').toLowerCase(),
  }),
});

export const resetPasswordSchema = z.object({
  body: z.object({
    token: z.string().min(16, 'Reset token is required').optional(),
    password: z.string().min(6, 'Password must be at least 6 characters').max(128),
  }),
  params: z
    .object({
      token: z.string().min(16, 'Reset token is required').optional(),
    })
    .optional(),
});

export const changePasswordSchema = z.object({
  body: z.object({
    currentPassword: z.string().min(1, 'Current password is required'),
    newPassword: z.string().min(6, 'New password must be at least 6 characters').max(128),
  }),
});

export const verifyOtpSchema = z.object({
  body: z.object({
    email: z.string().trim().email('Valid email is required').toLowerCase(),
    otp: z.string().length(6, '6-digit OTP is required'),
  }),
});

export const confirm2FASchema = z.object({
  body: z.object({
    otp: z.string().length(6, '6-digit OTP is required'),
  }),
});

export const profileUpdateSchema = z.object({
  body: z.object({
    name: z.string().trim().min(1, 'Name cannot be empty').max(100).optional(),
    phone: z.string().trim().max(20).optional(),
    avatar: z.string().url('Avatar must be a valid URL').optional(),
    address: z
      .object({
        street: z.string().optional(),
        city: z.string().optional(),
        state: z.string().optional(),
        country: z.string().optional(),
        zipCode: z.string().optional(),
      })
      .optional(),
    preferences: z
      .object({
        theme: z.enum(['light', 'dark', 'system']).optional(),
        language: z.string().optional(),
      })
      .optional(),
  }),
});

export const resendVerificationSchema = z.object({
  body: z.object({
    email: z.string().trim().email('Valid email is required').toLowerCase(),
  }),
});
