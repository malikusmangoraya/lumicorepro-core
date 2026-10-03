/**
 * RequireAuth — first line of defence for private routes.
 *
 * Backend authorization remains the real boundary (every request carries the JWT
 * and is re-checked server-side); this guard only stops an unauthenticated visitor
 * from rendering a private page shell and bouncing off failing API calls.
 *
 * Behaviour:
 *   - auth resolving → <PageSkeleton /> (never a blank screen)
 *   - unauthenticated → redirect to /login?next=<path+search>
 *   - authenticated  → render children
 *
 * `loading` is the resolving signal: AuthContext/AppContext hydrate the persisted
 * session synchronously from localStorage, so the only pending auth state is an
 * in-flight login / register / 2FA call.
 */
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import PageSkeleton from '../common/PageSkeleton';

/** Local, same-origin path only — blocks open-redirect payloads in `?next=`. */
export const loginRedirectFor = (location) => {
  const target = `${location?.pathname || '/'}${location?.search || ''}`;
  const safe = target.startsWith('/') && !target.startsWith('//') ? target : '/';
  return `/login?next=${encodeURIComponent(safe)}`;
};

export default function RequireAuth({ children }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) return <PageSkeleton />;
  if (!isAuthenticated) return <Navigate to={loginRedirectFor(location)} replace />;

  return children;
}
