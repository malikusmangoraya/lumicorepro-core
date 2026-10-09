/**
 * useApiQuery — server-state hook bound to the platform Axios client.
 * Dynamic import keeps static (API-less) builds green: falls back to a
 * relative fetch when the enterprise api.js interceptor is not present.
 */
import { useQuery } from '@tanstack/react-query';

const loadRequester = async () => {
  try {
    const mod = await import('../services/api');
    return mod.api || mod.default;
  } catch (e) {
    return {
      async get(path, cfg) {
        const res = await fetch(`/api${path}`, cfg);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      },
    };
  }
};

export default function useApiQuery(queryKey, path, options = {}) {
  return useQuery({
    queryKey,
    queryFn: async ({ signal }) => {
      const api = await loadRequester();
      const data = await api.get(path, { signal });
      return data?.data ?? data;
    },
    ...options,
  });
}
