/**
 * AppProviders — platform provider stack (QueryClientProvider root).
 * Platform TRD: server state must live on the TanStack cache cluster.
 */
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './queryClient';
import { CurrencyProvider } from '../context/CurrencyContext';

export default function AppProviders({ children }) {
  return (<QueryClientProvider client={queryClient}><CurrencyProvider>{children}</CurrencyProvider></QueryClientProvider>);
}
