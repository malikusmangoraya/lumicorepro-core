/**
 * RequireAdmin — role/plan gate for the /admin surface.
 *
 * Access is granted when the account matches any of:
 *   - a role in `roles` (default: admin / superadmin / owner)
 *   - a plan in `plans` (default: the plans sold with admin capabilities)
 *   - a permission listed in `permissions` and present on the user
 *
 * Insufficient access renders a real "Access denied" page, never a blank screen.
 * The backend still authorizes every admin endpoint — this is UX, not security.
 */
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { ShieldAlert, ArrowLeft, Home } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { loginRedirectFor } from './RequireAuth';
import PageSkeleton from '../common/PageSkeleton';
import { Button } from '../ui/Button';
// NOTE: no `ui/Card` import. Card pulls framer-motion, and this guard is imported
// statically by routes/index.jsx — that would put ~35 KB gzip back on first paint
// and fail the initial-JS budget in `npm run size` (see vite.config.js).

export const ADMIN_ROLES = ['admin', 'superadmin', 'super_admin', 'owner'];
export const ADMIN_PLANS = ['enterprise', 'business'];

const ROLE_FIELDS = ['role', 'userType', 'user_type'];
const PLAN_FIELDS = ['plan', 'planName', 'plan_name'];

const readRole = (user) => {
  for (const field of ROLE_FIELDS) {
    if (user?.[field]) return String(user[field]).toLowerCase();
  }
  return '';
};

const readPlan = (user) => {
  for (const field of PLAN_FIELDS) {
    if (user?.[field]) return String(user[field]).toLowerCase();
  }
  return String(user?.subscription?.plan || user?.subscription?.planName || '').toLowerCase();
};

/**
 * @param {object} user — the authenticated user (may be null)
 * @param {{roles?: string[], plans?: string[], permissions?: string[]}} [options]
 * @returns {boolean}
 */
export function hasAdminAccess(user, options = {}) {
  if (!user) return false;
  const { roles = ADMIN_ROLES, plans = ADMIN_PLANS, permissions = [] } = options;

  if (roles.includes(readRole(user))) return true;
  if (plans.length > 0 && plans.includes(readPlan(user))) return true;

  if (permissions.length > 0) {
    const granted = Array.isArray(user.permissions) ? user.permissions : [];
    return permissions.some((permission) => granted.includes(permission));
  }

  return false;
}

/** Real access-denied page (not a redirect loop, not a blank screen). */
export function AccessDenied({ role = '', plan = '' }) {
  const navigate = useNavigate();
  const account = [role && `role: ${role}`, plan && `plan: ${plan}`].filter(Boolean).join(' · ');

  return (
    <div className="flex min-h-[60vh] items-center justify-center px-4">
      <div className="w-full max-w-md space-y-4 rounded-xl border border-border bg-card p-6 text-center text-card-foreground shadow-sm">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-destructive/30 bg-destructive/10">
          <ShieldAlert className="h-7 w-7 text-destructive" aria-hidden="true" />
        </div>
        <h1 className="font-display text-2xl font-bold text-foreground">Access denied</h1>
        <p className="text-sm text-muted-foreground" role="alert">
          This area needs an administrator account. You are signed in
          {account ? ` with ${account}` : ' with an account that has no admin access'}, so the page
          was not loaded.
        </p>
        <p className="text-xs text-muted-foreground">
          Ask an administrator to raise your role, or sign in with an admin account.
        </p>
        <div className="flex flex-col items-center justify-center gap-3 pt-2 sm:flex-row">
          <Button variant="primary" leftIcon={ArrowLeft} onClick={() => navigate(-1)}>
            Go back
          </Button>
          <Button variant="outline" leftIcon={Home} onClick={() => navigate('/')}>
            Home
          </Button>
        </div>
      </div>
    </div>
  );
}

export default function RequireAdmin({ children, roles, plans, permissions }) {
  const { user, isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) return <PageSkeleton />;
  if (!isAuthenticated) return <Navigate to={loginRedirectFor(location)} replace />;

  if (!hasAdminAccess(user, { roles, plans, permissions })) {
    return <AccessDenied role={readRole(user)} plan={readPlan(user)} />;
  }

  return children;
}
