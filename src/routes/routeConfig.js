/**
 * Route configuration — machine-readable metadata for every primary
 * (non-template) route.
 *
 * The router itself stays in `index.jsx`; this is the metadata side of it.
 * Two consumers keep it honest so it cannot drift into fiction:
 *
 *   - `src/__tests__/routeConfig.test.js` asserts every path configured here
 *     exists in the router source and that no path is declared twice.
 *   - `e2e/routes.spec.js` smoke-visits every route flagged `smoke: true`.
 *
 * Fields:
 *   path   — router path relative to the '/' layout (must match index.jsx).
 *   access — 'public' | 'auth' | 'admin', matching the wrapper used in the
 *            router: plain, <Private>, <AdminOnly>. The backend remains the
 *            real authorization boundary; this documents the contract.
 *   smoke  — renders fully without a backend, so the e2e smoke pass visits it.
 */
export const routeConfig = [
  // ── Public ──────────────────────────────────────────────────────────────
  { path: '/', access: 'public', smoke: true },
  { path: 'marketing', access: 'public', smoke: true },
  { path: 'templates', access: 'public', smoke: true },
  { path: 'generate', access: 'public', smoke: false },
  { path: 'pricing', access: 'public', smoke: true },
  { path: 'login', access: 'public', smoke: true },
  { path: 'register', access: 'public', smoke: true },
  { path: 'forgot-password', access: 'public', smoke: true },
  { path: 'reset-password/:token', access: 'public', smoke: false },
  { path: 'verify-email/:token', access: 'public', smoke: false },
  { path: 'change-password', access: 'public', smoke: false },
  { path: 'oauth/callback', access: 'public', smoke: false },
  { path: 'gallery', access: 'public', smoke: false },
  { path: 'privacy', access: 'public', smoke: true },
  { path: 'terms', access: 'public', smoke: true },
  { path: 'refund', access: 'public', smoke: true },
  { path: 'boilerplate', access: 'public', smoke: false },
  { path: 'invite/:token', access: 'public', smoke: false },

  // ── Authenticated (RequireAuth in the router) ───────────────────────────
  { path: 'workspace', access: 'auth', smoke: false },
  { path: 'ai-dashboard', access: 'auth', smoke: false },
  { path: 'chat', access: 'auth', smoke: false },
  { path: 'billing', access: 'auth', smoke: false },
  { path: 'api-settings', access: 'auth', smoke: false },
  { path: 'profile', access: 'auth', smoke: false },
  { path: 'settings', access: 'auth', smoke: false },
  { path: 'orgs', access: 'auth', smoke: false },
  { path: 'orgs/:id', access: 'auth', smoke: false },
  { path: 'dashboard', access: 'auth', smoke: false },
  { path: 'notifications', access: 'auth', smoke: false },
  { path: 'onboarding', access: 'auth', smoke: false },

  // ── Admin (RequireAdmin in the router) ──────────────────────────────────
  { path: 'admin', access: 'admin', smoke: false },
  { path: 'admin/dashboard', access: 'admin', smoke: false },
  { path: 'admin/users', access: 'admin', smoke: false },
  { path: 'admin/audit', access: 'admin', smoke: false },
  { path: 'admin/settings', access: 'admin', smoke: false },
];

export default routeConfig;
