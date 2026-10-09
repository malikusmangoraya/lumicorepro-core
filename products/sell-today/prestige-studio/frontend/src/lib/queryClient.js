/**
 * Server-state cache cluster (TanStack React Query).
 * Platform TRD: single QueryClient — staleTime 5m, gcTime 30m, retry 2.
 */
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      gcTime: 30 * 60 * 1000,
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

export default queryClient;
