import React from 'react';
import { Chrome, Github, Facebook } from 'lucide-react';
import { cn } from '../../utils';
import Spinner from '../ui/Spinner';

const PROVIDERS = [
  {
    id: 'google',
    label: 'Google',
    icon: Chrome,
    hover: 'hover:border-foreground/30 hover:bg-muted',
  },
  {
    id: 'github',
    label: 'GitHub',
    icon: Github,
    hover: 'hover:border-foreground/30 hover:bg-muted',
  },
  {
    id: 'facebook',
    label: 'Facebook',
    icon: Facebook,
    hover: 'hover:border-foreground/30 hover:bg-muted',
  },
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
        <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
          {title}
        </span>
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
