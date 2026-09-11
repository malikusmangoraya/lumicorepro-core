import axios from 'axios';
import { getApiKey, isProviderEnabled } from './apiConfig';

// API Configuration from environment variables
const rawBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000';
const API_URL = rawBaseUrl.endsWith('/api') ? rawBaseUrl : `${rawBaseUrl.replace(/\/+$/, '')}/api`;
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT, 10) || 10000;

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  timeout: API_TIMEOUT,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Strip leading /api if the route already has it so we don't double to /api/api
    if (config.url && config.url.startsWith('/api/')) {
      config.url = config.url.replace(/^\/api/, '');
    }
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    // Add active organization header (multi-tenant)
    const orgId = localStorage.getItem('active_org_id');
    if (orgId) {
      config.headers['x-org-id'] = orgId;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor — single-flight 401 handling: try refresh once,
// then retry the original request; only redirect when refresh fails.
let isRefreshing = false;
let refreshQueue = [];

const processRefreshQueue = (token) => {
  refreshQueue.forEach(({ resolve, reject }) => {
    if (token) {
      const original = token;
      resolve(original);
    } else {
      reject(new Error('Session expired'));
    }
  });
  refreshQueue = [];
};

const redirectToLogin = () => {
  localStorage.removeItem('auth_token');
  if (!window.location.pathname.startsWith('/login')) {
    window.location.href = '/login';
  }
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (!error.response
      || error.response.status !== 401
      || original._retried
      || original.url.includes('/auth/login')
      || original.url.includes('/auth/refresh')) {
      return Promise.reject(error);
    }
    original._retried = true;

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        refreshQueue.push({
          resolve: (token) => {
            original.headers.Authorization = `Bearer ${token}`;
            resolve(api(original));
          },
          reject,
        });
      });
    }

    isRefreshing = true;
    try {
      const { data } = await api.post('/auth/refresh');
      const token = data?.token || data?.data?.token;
      if (!token) throw new Error('No refresh token returned');
      localStorage.setItem('auth_token', token);
      processRefreshQueue(token);
      original.headers.Authorization = `Bearer ${token}`;
      return api(original);
    } catch (_refreshError) {
      processRefreshQueue(null);
      redirectToLogin();
      return Promise.reject(error);
    } finally {
      isRefreshing = false;
    }
  }
);

// ==================== API Endpoints ====================

// Auth
export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  register: (userData) => api.post('/auth/register', userData),
  logout: () => api.post('/auth/logout'),
  refreshToken: () => api.post('/auth/refresh'),
  getProfile: () => api.get('/auth/profile'),
  updateProfile: (data) => api.put('/auth/profile', data),
};

// Users
export const usersAPI = {
  getAll: (params = {}) => api.get('/users', { params }),
  getById: (id) => api.get(`/users/${id}`),
  create: (data) => api.post('/users', data),
  update: (id, data) => api.put(`/users/${id}`, data),
  delete: (id) => api.delete(`/users/${id}`),
};

// Products (E-commerce)
export const productsAPI = {
  getAll: (params = {}) => api.get('/products', { params }),
  getById: (id) => api.get(`/products/${id}`),
  create: (data) => api.post('/products', data),
  update: (id, data) => api.put(`/products/${id}`, data),
  delete: (id) => api.delete(`/products/${id}`),
  search: (query) => api.get('/products/search', { params: { query } }),
  categories: () => api.get('/products/categories'),
};

// Orders
export const ordersAPI = {
  getAll: (params = {}) => api.get('/orders', { params }),
  getById: (id) => api.get(`/orders/${id}`),
  create: (data) => api.post('/orders', data),
  updateStatus: (id, status) => api.patch(`/orders/${id}/status`, { status }),
  delete: (id) => api.delete(`/orders/${id}`),
};

// Dashboard
export const dashboardAPI = {
  stats: () => api.get('/dashboard/stats'),
  reports: (params = {}) => api.get('/dashboard/reports', { params }),
  charts: (type) => api.get(`/dashboard/charts/${type}`),
  recentActivity: (limit = 10) => api.get('/dashboard/activity', { params: { limit } }),
};

// AI - Enhanced with dynamic API key support
export const aiAPI = {
  chat: (message, provider) => {
    const data = { message };
    if (provider) {
      const apiKey = getApiKey(provider);
      if (apiKey) {
        data.apiKey = apiKey;
      }
    }
    return api.post('/ai/chat', data);
  },
  analyze: (data, provider) => {
    if (provider) {
      const apiKey = getApiKey(provider);
      if (apiKey) {
        data.apiKey = apiKey;
      }
    }
    return api.post('/ai/analyze', data);
  },
  generate: (prompt, provider) => {
    const data = { prompt };
    if (provider) {
      const apiKey = getApiKey(provider);
      if (apiKey) {
        data.apiKey = apiKey;
      }
    }
    return api.post('/ai/generate', data);
  },
  completions: (input, provider) => {
    const data = { input };
    if (provider) {
      const apiKey = getApiKey(provider);
      if (apiKey) {
        data.apiKey = apiKey;
      }
    }
    return api.post('/ai/completions', data);
  },
  // Check which AI providers are available
  availableProviders: () => {
    return {
      gemini: isProviderEnabled('gemini'),
      deepseek: isProviderEnabled('deepseek'),
      openrouter: isProviderEnabled('openrouter'),
    };
  },
};

// Real AI Agent Generation Engine (FastAPI Pipeline)
export const aiAgentAPI = {
  generate: (payload) => api.post('/ai/generate', payload),
  getRunStatus: (runId) => api.get(`/ai/runs/${runId}`),
  getDownloadUrl: (runId) => {
    const raw = import.meta.env.VITE_API_URL || 'http://localhost:5000';
    const base = raw.endsWith('/api') ? raw : `${raw.replace(/\/+$/, '')}/api`;
    return `${base}/ai/download/${runId}`;
  },
  checkHealth: () => api.get('/ai/health'),
  analyzeVision: (payload) => api.post('/ai/vision/analyze', payload),
  visionChat: (payload) => api.post('/ai/chat', payload),
  createPreview: (runId) => api.post('/ai/preview', { run_id: runId }),
  deployRun: (runId, platform = 'vercel') => api.post('/ai/deploy', { run_id: runId, platform }),
  connectDomain: (payload) => api.post('/ai/deploy/domain', payload),
};

// Payments
export const paymentsAPI = {
  getConfig: () => api.get('/payments/config'),
  createIntent: (data) => api.post('/payments/create-intent', data),
  confirm: (data) => api.post('/payments/confirm', data),
  refund: (data) => api.post('/payments/refund', data),
  checkout: (data) => api.post('/payments/checkout', data),
  portal: () => api.post('/payments/portal'),
};

export const plansAPI = {
  list: () => api.get('/plans'),
};

export const subscriptionsAPI = {
  list: () => api.get('/subscriptions'),
  create: (planId) => api.post('/subscriptions', { planId }),
  cancel: (id) => api.patch(`/subscriptions/${id}/cancel`),
  remove: (id) => api.delete(`/subscriptions/${id}`),
};

export const previewAPI = {
  create: (runId) => api.post('/ai/preview', { run_id: runId }),
  deploy: (runId, platform = 'vercel') => api.post('/ai/deploy', { run_id: runId, platform }),
};

// License validation (self-hosted, free)
export const licenseAPI = {
  validate: (key) => api.post('/license/validate', { key }),
  metadata: () => api.get('/license/metadata'),
};

/** Validate a license key stored in localStorage. Never blocks the UI;
 * returns { valid:false } when offline/unconfigured so the app still works. */
export const checkStoredLicense = async () => {
  const key = localStorage.getItem('lmc_license_key');
  if (!key) return { valid: false, status: 'no_key' };
  try {
    const { data } = await licenseAPI.validate(key);
    return data?.valid ? { valid: true, status: 'active' } : { valid: false, status: data?.status || 'invalid' };
  } catch (e) {
    return { valid: false, status: 'offline' };
  }
};

/**
 * Resolve a preview URL returned by the agent into a URL the browser can load.
 * - Absolute HTTP(S) URLs (e.g. a production preview base) are kept as-is.
 * - Relative paths (e.g. `/preview/slug`) are rewritten through the Express
 *   proxy at `${API_URL}/ai/preview/{slug}` so the iframe works from the
 *   frontend origin on both dev and deployed backends.
 */
export const resolvePreviewUrl = (raw, slug) => {
  if (!raw) return raw;
  try {
    const parsed = new URL(raw);
    if (parsed.protocol === 'http:' || parsed.protocol === 'https:') return raw;
  } catch (e) {
    /* relative path — rewrite below */
  }
  const base = API_URL.replace(/\/api\/?$/, '');
  const previewSlug = slug || raw.split('/').pop() || 'preview';
  return `${base}/api/ai/preview/${encodeURIComponent(previewSlug)}`;
};

// Notifications
export const notificationsAPI = {
  getAll: (params = {}) => api.get('/notifications', { params }),
  create: (data) => api.post('/notifications', data),
  markRead: (id) => api.patch(`/notifications/${id}/read`),
  markAllRead: () => api.patch('/notifications/read-all'),
  delete: (id) => api.delete(`/notifications/${id}`),
};

// Search
export const searchAPI = {
  global: (params) => api.get('/search', { params }),
  autocomplete: (q) => api.get('/search/autocomplete', { params: { q } }),
  trending: () => api.get('/search/trending'),
};

// Uploads
export const uploadsAPI = {
  uploadSingle: (formData) =>
    api.post('/uploads/single', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  uploadMultiple: (formData) =>
    api.post('/uploads/multiple', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  deleteFile: (filename) => api.delete(`/uploads/${filename}`),
};

// Analytics
export const analyticsAPI = {
  dashboard: () => api.get('/analytics/dashboard'),
  sales: (days = 30) => api.get('/analytics/sales', { params: { days } }),
  topProducts: (limit = 5) => api.get('/analytics/top-products', { params: { limit } }),
  userGrowth: () => api.get('/analytics/user-growth'),
  categoryDistribution: () => api.get('/analytics/category-distribution'),
};

// Business
export const businessAPI = {
  analytics: (params = {}) => api.get('/business/analytics', { params }),
  reports: () => api.get('/business/reports'),
  settings: () => api.get('/business/settings'),
  updateSettings: (data) => api.put('/business/settings', data),
};

export default api;
