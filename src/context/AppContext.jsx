import { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import i18n from '../i18n';
import { updateDocumentDirection } from '../i18n/rtlHelper';

export const AppContext = createContext();

export function useAppContext() {
  const ctx = useContext(AppContext);
  if (!ctx) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return ctx;
}

export function AppProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    if (typeof window !== 'undefined') {
      return (
        localStorage.getItem('theme') ||
        (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
      );
    }
    return 'dark';
  });

  const [language, setLanguageState] = useState(() => {
    if (typeof window === 'undefined') return 'en';
    const saved = localStorage.getItem('i18nextLng');
    if (saved) return saved;
    const detected = i18n.language || i18n.resolvedLanguage;
    const base = (detected || 'en').split('-')[0].toLowerCase();
    const supported =
      i18n.languages && Array.isArray(i18n.languages)
        ? i18n.languages
        : ['en', 'es', 'fr', 'de', 'ar', 'zh', 'ja', 'ur', 'ko', 'pt', 'it', 'hi', 'tr'];
    return supported.includes(base) ? base : 'en';
  });

  const [auth, setAuth] = useState(() => {
    try {
      const saved = localStorage.getItem('auth');
      return saved
        ? JSON.parse(saved)
        : { user: null, token: localStorage.getItem('auth_token') || null };
    } catch {
      return { user: null, token: null };
    }
  });

  const [notifications, setNotifications] = useState([]);

  // Handle language switch + RTL direction update
  const setLanguage = useCallback((lang) => {
    const safeLang = lang || 'en';
    setLanguageState(safeLang);
    i18n.changeLanguage(safeLang);
    localStorage.setItem('i18nextLng', safeLang);
    document.documentElement.lang = safeLang;
    updateDocumentDirection(safeLang);
  }, []);

  useEffect(() => {
    const safeLang = language || 'en';
    document.documentElement.lang = safeLang;
    updateDocumentDirection(safeLang);
  }, [language]);

  // Synchronize auth changes across tabs and with AuthContext
  useEffect(() => {
    const syncAuth = () => {
      try {
        const saved = localStorage.getItem('auth');
        const token = localStorage.getItem('auth_token');
        if (saved) {
          const parsed = JSON.parse(saved);
          setAuth({ user: parsed.user, token: parsed.token || token });
        } else if (token) {
          setAuth((prev) => ({ ...prev, token }));
        } else {
          setAuth({ user: null, token: null });
        }
      } catch {
        setAuth({ user: null, token: null });
      }
    };

    window.addEventListener('storage', syncAuth);
    window.addEventListener('auth-change', syncAuth);
    return () => {
      window.removeEventListener('storage', syncAuth);
      window.removeEventListener('auth-change', syncAuth);
    };
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  }, []);

  const addNotification = useCallback((message, type = 'info') => {
    const id = Date.now();
    setNotifications((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setNotifications((prev) => prev.filter((n) => n.id !== id));
    }, 4000);
  }, []);

  const login = useCallback(
    (user, token) => {
      const payload = { user, token };
      setAuth(payload);
      if (token) localStorage.setItem('auth_token', token);
      localStorage.setItem('auth', JSON.stringify(payload));
      window.dispatchEvent(new Event('auth-change'));
      addNotification('Logged in successfully', 'success');
    },
    [addNotification]
  );

  const logout = useCallback(() => {
    setAuth({ user: null, token: null });
    localStorage.removeItem('auth');
    localStorage.removeItem('auth_token');
    window.dispatchEvent(new Event('auth-change'));
    addNotification('Logged out', 'info');
  }, [addNotification]);

  const dismissNotification = useCallback((id) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const value = useMemo(
    () => ({
      theme,
      toggleTheme,
      isDark: theme === 'dark',
      isDarkMode: theme === 'dark',
      toggleDarkMode: toggleTheme,
      language,
      setLanguage,
      auth,
      user: auth.user,
      token: auth.token,
      login,
      logout,
      isAuthenticated: !!auth.token,
      notifications,
      addNotification,
      dismissNotification,
    }),
    [
      theme,
      language,
      auth,
      notifications,
      toggleTheme,
      setLanguage,
      login,
      logout,
      addNotification,
      dismissNotification,
    ]
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}
