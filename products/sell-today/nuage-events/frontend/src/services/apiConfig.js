/**
 * API configuration — enterprise full-stack mode.
 * The Axios instance talks to RELATIVE /api/* sub-routes; in production the
 * Nginx gateway proxies /api/* to the Express upstream (see nginx/nginx.conf).
 */
export const getApiConfig = () => {
  const raw = import.meta.env.VITE_API_URL || '/api';
  return {
    API_URL: raw.endsWith('/') ? raw.slice(0, -1) : raw,
    API_TIMEOUT: Number(import.meta.env.VITE_API_TIMEOUT) || 12000,
  };
};
