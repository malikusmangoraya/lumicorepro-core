import { RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MotionConfig } from 'framer-motion';
import ErrorBoundary from './components/common/ErrorBoundary';
import ThemeProvider from './components/common/ThemeProvider';
import { Analytics, CookieConsent } from './components/common';
import './i18n';
import { AppProvider, AuthProvider, CartProvider, CurrencyProvider, OrgProvider } from './context';
import { router } from './routes';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <ErrorBoundary>
      <MotionConfig reducedMotion="user">
        <QueryClientProvider client={queryClient}>
          <AppProvider>
            <ThemeProvider>
              <AuthProvider>
                <CartProvider>
                  <CurrencyProvider>
                    <OrgProvider>
                      <RouterProvider router={router} />
                      <Analytics />
                      <CookieConsent />
                    </OrgProvider>
                  </CurrencyProvider>
                </CartProvider>
              </AuthProvider>
            </ThemeProvider>
          </AppProvider>
        </QueryClientProvider>
      </MotionConfig>
    </ErrorBoundary>
  );
}

export default App;
