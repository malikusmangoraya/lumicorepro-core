import test, { afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { clearAuthSession, getAuthToken, requireAuth, saveAuthSession } from './auth.js';

const values = new Map();
let currentPath = '/generate';
let redirectedTo;
globalThis.window = {
  localStorage: {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, String(value)),
    removeItem: (key) => values.delete(key),
  },
  get location() {
    return {
      get pathname() { return currentPath.split('?')[0]; },
      get search() { return currentPath.includes('?') ? currentPath.slice(currentPath.indexOf('?')) : ''; },
      replace: (destination) => { redirectedTo = destination; },
    };
  },
};

afterEach(() => {
  clearAuthSession();
  currentPath = '/generate';
  redirectedTo = undefined;
});

test('saves and clears the token and user session', () => {
  saveAuthSession('signed-token', { email: 'writer@example.com' });

  assert.equal(getAuthToken(), 'signed-token');
  assert.deepEqual(JSON.parse(window.localStorage.getItem('user')), {
    email: 'writer@example.com',
  });

  clearAuthSession();
  assert.equal(getAuthToken(), null);
  assert.equal(window.localStorage.getItem('user'), null);
});

test('redirects signed-out users to login and preserves the workspace destination', () => {
  currentPath = '/generate/history?filter=recent';

  assert.equal(requireAuth(), false);
  assert.equal(redirectedTo, '/login?next=%2Fgenerate%2Fhistory%3Ffilter%3Drecent');
});

test('allows a signed-in user into the workspace', () => {
  saveAuthSession('signed-token', { email: 'writer@example.com' });

  assert.equal(requireAuth(), true);
  assert.equal(redirectedTo, undefined);
});
