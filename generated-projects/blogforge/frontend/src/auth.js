const TOKEN_KEY = 'token';
const USER_KEY = 'user';

export function getAuthToken() {
  return window.localStorage.getItem(TOKEN_KEY);
}

export function saveAuthSession(token, user) {
  window.localStorage.setItem(TOKEN_KEY, token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuthSession() {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}

export function requireAuth() {
  if (!getAuthToken()) {
    const destination = `${window.location.pathname}${window.location.search}`;
    const next = destination.startsWith('/generate') ? destination : '/generate';
    window.location.replace(`/login?next=${encodeURIComponent(next)}`);
    return false;
  }
  return true;
}
