import { RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider, QueryCache } from '@tanstack/react-query';
import { lazy, Suspense, useState, useEffect, useCallback } from 'react';
import ErrorBoundary from './components/common/ErrorBoundary';
import ThemeProvider from './components/common/ThemeProvider';
import Analytics from './components/common/Analytics';
import CookieConsent from './components/common/CookieConsent';
import ToastRegion from './components/common/ToastRegion';
import './i18n';
import './styles/advanced-effects.css';
import { AppProvider } from './context/AppContext';
import { AuthProvider } from './context/AuthContext';
import { CurrencyProvider } from './context/CurrencyContext';
import { OrgProvider } from './context/OrgContext';
import { NotificationProvider, useNotifications } from './context/NotificationContext';
import { notifyError } from './services/notificationBus';
import { router } from './routes';

// Documented React Query standard (AGENTS.md §8): stale 5min, gc 30min, 2 retries.
// Query errors are surfaced through the toast region instead of being swallowed —
// the cache callbacks live outside React, so they go through notificationBus.
const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error) => notifyError(error),
  }),
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      gcTime: 30 * 60 * 1000,
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

const CommandPalette = lazy(() => import('./components/advanced/CommandPalette'));

function AppCommandPalette({ isOpen, onClose }) {
  const { addNotification } = useNotifications();

  const handleExecute = useCallback(
    (command) => {
      addNotification?.(command?.label || 'Command executed', 'info');
    },
    [addNotification]
  );

  return (
    <Suspense fallback={null}>
      <CommandPalette isOpen={isOpen} onClose={onClose} onExecute={handleExecute} />
    </Suspense>
  );
}

function App() {
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

  // Global keyboard shortcut for Command Palette (Cmd+K / Ctrl+K)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCommandPaletteOpen((prev) => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AppProvider>
          <ThemeProvider>
            <NotificationProvider>
              <AuthProvider>
                <CurrencyProvider>
                  <OrgProvider>
                    <RouterProvider router={router} />
                    <Analytics />
                    <CookieConsent />
                    <ToastRegion />
                    {commandPaletteOpen && (
                      <AppCommandPalette isOpen onClose={() => setCommandPaletteOpen(false)} />
                    )}
                  </OrgProvider>
                </CurrencyProvider>
              </AuthProvider>
            </NotificationProvider>
          </ThemeProvider>
        </AppProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
