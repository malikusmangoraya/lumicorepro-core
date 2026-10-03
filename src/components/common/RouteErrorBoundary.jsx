import { useCallback } from 'react';
import { isRouteErrorResponse, useNavigate, useRouteError } from 'react-router-dom';
import { AlertTriangle, RotateCcw, ArrowLeft } from 'lucide-react';

/**
 * RouteErrorBoundary — the `errorElement` for React Router routes.
 * Must read the error via `useRouteError()` because an errorElement never
 * receives `children`, so the class-based ErrorBoundary is not usable here.
 */
export default function RouteErrorBoundary() {
  const error = useRouteError();
  const navigate = useNavigate();

  const goHome = useCallback(() => navigate('/', { replace: true }), [navigate]);
  const retry = useCallback(() => navigate(0), [navigate]);

  const isResponse = isRouteErrorResponse(error);
  const heading = isResponse ? `Page unavailable (${error.status})` : 'Something went wrong';
  const message = isResponse
    ? 'We could not load this page. It may have moved or is temporarily offline.'
    : 'An unexpected error occurred while loading this page.';

  const detail = isResponse
    ? error.statusText || String(error.status)
    : (error instanceof Error && error.message) || 'Unknown error';

  return (
    <div className="flex items-center justify-center min-h-[50vh] px-4">
      <div
        role="alert"
        aria-live="assertive"
        className="text-center max-w-md animate-fade-in-up"
      >
        <div className="mx-auto w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center mb-4">
          <AlertTriangle className="h-6 w-6 text-red-500" aria-hidden="true" />
        </div>
        <h2 className="font-display text-xl font-semibold mb-2">{heading}</h2>
        <p className="text-muted-foreground text-sm mb-4">{message}</p>
        <div className="flex items-center justify-center gap-3">
          <button
            type="button"
            onClick={goHome}
            className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Go home
          </button>
          <button
            type="button"
            onClick={retry}
            className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <RotateCcw className="h-4 w-4" aria-hidden="true" />
            Try again
          </button>
        </div>
        {import.meta.env.DEV && (
          <details className="mt-6 text-left">
            <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
              Error details
            </summary>
            <pre className="mt-2 text-xs text-muted-foreground bg-muted/50 rounded-lg p-3 overflow-auto max-h-48 whitespace-pre-wrap break-words">
              {detail}
            </pre>
          </details>
        )}
      </div>
    </div>
  );
}
