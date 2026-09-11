import { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import api from '../../services/api';

/**
 * SetupGate — checks whether the buyer has finished onboarding.
 * When SystemConfig is empty (fresh deployment), any non-authenticated landing
 * on '/' or '/admin' is redirected to the Setup Wizard so the buyer configures
 * the site from the browser instead of a terminal.
 *
 * Fails open: if the backend is unreachable (offline/dev) or setup is complete,
 * normal navigation continues untouched.
 */
const IGNORED_PATHS = ['/setup', '/login', '/register', '/privacy', '/terms', '/refund', '/reset-password'];

export default function SetupGate({ children }) {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      const path = location.pathname;
      if (IGNORED_PATHS.some((p) => path.startsWith(p))) return;

      try {
        const res = await api.get('/settings/status', { timeout: 4000 });
        const data = res.data?.data;
        if (!cancelled && data?.needsSetup === true) {
          navigate('/setup', { replace: true });
        }
      } catch {
        /* backend offline / dev — never lock users out */
      }
    };

    // Only run once per mount and only on root/admin paths to keep the check cheap
    const isRoot = location.pathname === '/' || location.pathname.startsWith('/admin');
    if (isRoot) run();
  }, [location.pathname]);

  return children;
}