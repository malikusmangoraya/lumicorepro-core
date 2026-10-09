/**
 * Pre-configured Axios instance — enterprise full-stack mode.
 * baseURL defaults to the relative /api route served by the Nginx gateway.
 * Request interceptor attaches the JWT; response interceptor handles 401s.
 */
import axios from 'axios';
import { getApiConfig } from './apiConfig';

const { API_URL, API_TIMEOUT } = getApiConfig();

const api = axios.create({
  baseURL: API_URL,
  timeout: API_TIMEOUT,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use(
  (config) => {
    if (config.url && config.url.startsWith('/api/')) {
      config.url = config.url.replace(/^\/api/, '');
    }
    const token = localStorage.getItem('auth_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
