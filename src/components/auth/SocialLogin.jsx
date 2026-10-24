import React from 'react';
import { cn } from '../../utils';
import Spinner from '../ui/Spinner';

/**
 * Brand marks are inline SVGs: lucide-react no longer ships brand icons
 * (Chrome/Github/Facebook were undefined, which crashed the component with
 * "Element type is invalid"). Props mirror lucide so the render code below is
 * unchanged.
 */
const GoogleIcon = (props) => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...props}>
    <path d="M21.35 11.1h-9.17v2.73h6.51c-.33 3.81-3.5 5.44-6.5 5.44C8.36 19.27 5 16.25 5 12c0-4.1 3.2-7.27 7.2-7.27 3.09 0 4.9 1.97 4.9 1.97L19 4.72S16.56 2 12.1 2C6.42 2 2.03 6.8 2.03 12c0 5.05 4.13 10 10.22 10 5.35 0 9.25-3.67 9.25-9.09 0-1.15-.15-1.81-.15-1.81Z" />
  </svg>
);

const GithubIcon = (props) => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...props}>
    <path d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.55v-2.15c-3.2.7-3.87-1.36-3.87-1.36-.52-1.34-1.28-1.7-1.28-1.7-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.77 2.7 1.26 3.36.96.1-.75.4-1.26.73-1.55-2.55-.29-5.24-1.28-5.24-5.68 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11 11 0 0 1 5.79 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.12 3.05.74.81 1.18 1.84 1.18 3.1 0 4.41-2.69 5.38-5.25 5.67.41.35.78 1.05.78 2.12v3.15c0 .3.21.66.8.55A11.51 11.51 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5Z" />
  </svg>
);

const FacebookIcon = (props) => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...props}>
    <path d="M22 12.06C22 6.5 17.52 2 12 2S2 6.5 2 12.06c0 5.02 3.66 9.18 8.44 9.94v-7.03H7.9v-2.91h2.54V9.85c0-2.52 1.49-3.92 3.78-3.92 1.09 0 2.24.2 2.24.2v2.47h-1.26c-1.24 0-1.63.78-1.63 1.57v1.89h2.78l-.45 2.91h-2.33V22c4.78-.76 8.43-4.92 8.43-9.94Z" />
  </svg>
);

const PROVIDERS = [
  { id: 'google', label: 'Google', icon: GoogleIcon, hover: 'hover:border-foreground/30 hover:bg-muted' },
  { id: 'github', label: 'GitHub', icon: GithubIcon, hover: 'hover:border-foreground/30 hover:bg-muted' },
  { id: 'facebook', label: 'Facebook', icon: FacebookIcon, hover: 'hover:border-foreground/30 hover:bg-muted' },
];

const SocialLogin = ({
  onProviderClick,
  title = 'Or continue with',
  className = '',
  loadingProvider = '',
}) => {
  return (
    <div className={cn('w-full max-w-md space-y-3', className)}>
      <div className="flex items-center gap-3">
        <span className="h-px flex-1 bg-border" aria-hidden="true" />
        <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{title}</span>
        <span className="h-px flex-1 bg-border" aria-hidden="true" />
      </div>
      <div className="grid grid-cols-3 gap-3">
        {PROVIDERS.map(({ id, label, icon: Icon, hover }) => (
          <button
            key={id}
            type="button"
            onClick={() => typeof onProviderClick === 'function' && onProviderClick(id)}
            disabled={Boolean(loadingProvider) && loadingProvider !== id}
            className={cn(
              'flex items-center justify-center gap-2 rounded-lg border bg-background px-3 py-2.5 text-sm font-medium text-foreground transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary/40 disabled:cursor-not-allowed disabled:opacity-60',
              hover
            )}
          >
            {loadingProvider === id ? (
              <Spinner size="sm" />
            ) : (
              <Icon className="h-4 w-4" aria-hidden="true" />
            )}
            <span className="sr-only">{label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default SocialLogin;