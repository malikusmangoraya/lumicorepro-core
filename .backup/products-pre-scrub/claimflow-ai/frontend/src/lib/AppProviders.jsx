/**
 * AppProviders — platform provider stack (QueryClientProvider root).
 * Platform TRD: server state must live on the TanStack cache cluster.
 */
import { QueryClientProvider } from '@tanstack/react-query';
import { CurrencyProvider } from '../context/CurrencyContext';
import { queryClient } from './queryClient';

export default function AppProviders({ children }) {
  return (
    <CurrencyProvider>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </CurrencyProvider>
  )
}
