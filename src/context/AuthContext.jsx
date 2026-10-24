/**
 * AuthContext — thin adapter over AppContext.
 *
 * AppContext is the single source of truth for auth state (user, token,
 * isAuthenticated, login, logout). This context wraps it in a familiar
 * useAuth() API for components that prefer the named hook, and adds the
 * register() action which only belongs to the auth flow.
 *
 * This eliminates the previous dual-state where both AppContext and
 * AuthContext maintained separate user/token state and synced via events.
 */
import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { useAppContext } from './AppContext';
import authService from '../services/auth';
import { trackEvent, AnalyticsEvents } from '../utils/analytics';

const AuthContext = createContext(null);

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

export function AuthProvider({ children }) {
  const app = useAppContext();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const login = useCallback(
    async (credentials) => {
      setLoading(true);
      setError(null);
      try {
        // Try real backend first
        try {
          const res = await authService.login(credentials);
          const data = res.data;

          if (data?.requires2FA) {
            return { requires2FA: true, user: data.user, message: data.message };
          }

          const u = data?.user || data?.data?.user;
          const t = data?.token || data?.data?.token;
          if (u && t) {
            app.login(u, t);
            return { user: u, token: t };
          }
        } catch (apiErr) {
          const isConfiguredDemo =
            import.meta.env.DEV &&
            credentials?.email?.toLowerCase() === import.meta.env.VITE_DEMO_ADMIN_EMAIL?.toLowerCase() &&
            credentials?.password === import.meta.env.VITE_DEMO_USER_PASSWORD;
          if (isConfiguredDemo) {
            const demo = {
              id: 2,
              name: 'Admin User',
              email: credentials.email.toLowerCase(),
              role: 'admin',
              avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150',
            };
            const t = 'local-demo-admin-token';
            app.login(demo, t);
            return { user: demo, token: t, demo: true };
          }
          throw new Error(
            apiErr.response?.data?.error ||
              apiErr.response?.data?.message ||
              apiErr.message ||
              'Login failed. Check your email and password.',
            { cause: apiErr }
          );
        }

        throw new Error('Invalid response from authentication server', {
          cause: new Error('No valid token in response'),
        });
      } catch (err) {
        const msg = err.message || 'Login failed';
        setError(msg);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [app]
  );

  const register = useCallback(
    async (payload) => {
      setLoading(true);
      setError(null);
      try {
        try {
          const res = await authService.register(payload);
          const data = res.data;
          const u = data?.user || data?.data?.user;
          const t = data?.token || data?.data?.token;
          if (u && t) {
            app.login(u, t);
            trackEvent(AnalyticsEvents.SIGNUP);
            return { user: u, token: t };
          }
        } catch (apiErr) {
          throw new Error(
            apiErr.response?.data?.error ||
              apiErr.response?.data?.message ||
              apiErr.message ||
              'Registration failed. Please start the backend and try again.',
            { cause: apiErr }
          );
        }
        throw new Error('Registration failed');
      } catch (err) {
        const msg = err.message || 'Registration failed';
        setError(msg);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [app]
  );

  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } catch {
      /* ignore offline logout errors */
    }
    app.logout();
  }, [app]);

  // ── Account security actions: verify / reset / 2FA ──────────────────────
  const verifyEmail = useCallback(async (token) => {
    const res = await authService.verifyEmail(token);
    return res.data;
  }, []);

  const resendVerification = useCallback(
    async (email) => {
      const res = await authService.resendVerification(email);
      return res.data;
    },
    []
  );

  const forgotPassword = useCallback(async (email) => {
    const res = await authService.forgotPassword(email);
    return res.data;
  }, []);

  const resetPassword = useCallback(async (token, password) => {
    const res = await authService.resetPassword(token, password);
    return res.data;
  }, []);

  const changePassword = useCallback(
    async (data) => {
      const res = await authService.changePassword(data);
      return res.data;
    },
    []
  );

  const setup2FA = useCallback(async (data) => {
    const res = await authService.setup2FA(data);
    return res.data;
  }, []);

  const confirm2FA = useCallback(async (otp) => {
    const res = await authService.confirm2FA(otp);
    return res.data;
  }, []);

  const verify2FALogin = useCallback(async (data) => {
    const res = await authService.verify2FALogin(data);
    return res.data;
  }, []);

  const value = useMemo(
    () => ({
      // State — delegated from AppContext (single source of truth)
      user: app.user,
      token: app.token,
      isAuthenticated: app.isAuthenticated,
      // Actions
      loading,
      error,
      login,
      register,
      logout,
      setError,
      // Account security
      verifyEmail,
      resendVerification,
      forgotPassword,
      resetPassword,
      changePassword,
      setup2FA,
      confirm2FA,
      verify2FALogin,
    }),
    [
      app.user,
      app.token,
      app.isAuthenticated,
      loading,
      error,
      login,
      register,
      logout,
      verifyEmail,
      resendVerification,
      forgotPassword,
      resetPassword,
      changePassword,
      setup2FA,
      confirm2FA,
      verify2FALogin,
    ]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export default AuthContext;
