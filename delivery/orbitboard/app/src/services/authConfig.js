function isServerOnlyKey(key) {
  if (key.startsWith('sb_secret_')) return true;

  const payload = key.split('.')[1];
  if (!payload) return false;

  try {
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
    const decoded = atob(base64.padEnd(Math.ceil(base64.length / 4) * 4, '='));
    const { role } = JSON.parse(decoded);
    return role === 'service_role' || role === 'supabase_admin';
  } catch {
    return false;
  }
}

export function createAuthConfig(url, anonKey) {
  const normalizedUrl = typeof url === 'string' ? url.trim().replace(/\/+$/, '') : '';
  const normalizedKey = typeof anonKey === 'string' ? anonKey.trim() : '';

  if (!normalizedUrl || !normalizedKey) {
    return { configured: false, reason: 'missing' };
  }
  if (isServerOnlyKey(normalizedKey)) {
    return { configured: false, reason: 'invalid-key' };
  }

  try {
    const parsedUrl = new URL(normalizedUrl);
    const secure = parsedUrl.protocol === 'https:';
    const local = parsedUrl.protocol === 'http:' &&
      ['localhost', '127.0.0.1'].includes(parsedUrl.hostname);

    if ((!secure && !local) || parsedUrl.username || parsedUrl.password) {
      return { configured: false, reason: 'invalid-url' };
    }

    return {
      configured: true,
      url: normalizedUrl,
      anonKey: normalizedKey,
    };
  } catch {
    return { configured: false, reason: 'invalid-url' };
  }
}

export const authConfig = createAuthConfig(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY,
);
