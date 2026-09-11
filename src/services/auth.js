/**
 * LumicorePro — Auth Service
 * Wraps all authentication API calls.
 * Base URL is set by the central api.js axios instance (/api prefix).
 */
import api from './api';

const authService = {
  login: (credentials) => api.post('/auth/login', credentials),
  register: (userData) => api.post('/auth/register', userData),
  logout: () => api.post('/auth/logout'),

  // Correct endpoint: /auth/refresh (NOT /auth/refresh-token)
  refreshToken: () => api.post('/auth/refresh'),

  getProfile: () => api.get('/auth/profile'),
  updateProfile: (data) => api.put('/auth/profile', data),

  forgotPassword: (email) => api.post('/auth/forgot-password', { email }),
  resetPassword: (token, password) => api.post(`/auth/reset-password/${token}`, { password }),

  // Change password for an authenticated user
  changePassword: (data) => api.put('/auth/change-password', data),

  // Email verification
  verifyEmail: (token) => api.get(`/auth/verify-email/${token}`),
  resendVerification: (email) => api.post('/auth/resend-verification', { email }),

  // 2FA
  setup2FA: (data) => api.post('/auth/2fa/setup', data),
  confirm2FA: (otp) => api.post('/auth/2fa/confirm', { otp }),
  sendOTP: () => api.post('/auth/2fa/send-otp'),
  verify2FALogin: (data) => api.post('/auth/2fa/login-verify', data),
};

export default authService;
