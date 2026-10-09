import { Component } from 'react';
import { AlertTriangle, RotateCcw, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import { captureError } from '../../utils/sentry';

/**
 * ErrorBoundary — catches React render errors and shows a user-friendly fallback.
 * Use as a wrapper around route groups, template groups, or the entire app.
 */
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    // Report to Sentry when configured; no-op locally (see utils/sentry.js).
    captureError(error, { componentStack: errorInfo?.componentStack?.slice(0, 2000) });
  }

  handleReset = () => {
    this.setState({ error: null, errorInfo: null });
  };

  render() {
    if (this.state.error) {
      return (
        <div className="flex items-center justify-center min-h-[50vh] px-4">
          <div className="text-center max-w-md animate-fade-in-up">
            <div className="mx-auto w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center mb-4">
              <AlertTriangle className="h-6 w-6 text-red-500" />
            </div>
            <h2 className="font-display text-xl font-semibold mb-2">Something went wrong</h2>
            <p className="text-muted-foreground text-sm mb-4">
              {this.state.error.message || 'An unexpected error occurred while loading this page.'}
            </p>
            <div className="flex items-center justify-center gap-3">
              <Link
                to="/"
                className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                <ArrowLeft className="h-4 w-4" />
                Go home
              </Link>
              <button
                type="button"
                onClick={this.handleReset}
                className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                <RotateCcw className="h-4 w-4" />
                Try again
              </button>
            </div>
            {import.meta.env.DEV && this.state.errorInfo && (
              <details className="mt-6 text-left">
                <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
                  Component Stack
                </summary>
                <pre className="mt-2 text-xs text-muted-foreground bg-muted/50 rounded-lg p-3 overflow-auto max-h-48">
                  {this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
