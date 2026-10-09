import React, { useEffect, useState } from 'react';
import { Smartphone, X, Download } from 'lucide-react';
import { cn } from '../../utils';

const isIOS = () => /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;

const PWAInstallBanner = ({
  appName = 'Install our app',
  description = 'Add to your home screen for the fastest experience.',
  position = 'bottom',
  storageKey = 'pwa_install_dismissed',
  className = '',
}) => {
  const [installPrompt, setInstallPrompt] = useState(null);
  const [visible, setVisible] = useState(false);
  const [isIos, setIsIos] = useState(false);

  useEffect(() => {
    setIsIos(isIOS());
    const dismissed = (() => {
      try {
        return localStorage.getItem(storageKey) === '1';
      } catch (e) {
        return false;
      }
    })();
    if (dismissed) return undefined;

    const handler = (e) => {
      e.preventDefault();
      setInstallPrompt(e);
      setVisible(true);
    };
    window.addEventListener('beforeinstallprompt', handler);

    const navVisible = () => {
      if (!document.hidden) setVisible(true);
    };
    document.addEventListener('visibilitychange', navVisible);

    if (isIOS()) setVisible(true);

    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
      document.removeEventListener('visibilitychange', navVisible);
    };
  }, [storageKey]);

  const dismiss = () => {
    setVisible(false);
    try {
      localStorage.setItem(storageKey, '1');
    } catch (e) {
      /* storage unavailable */
    }
  };

  const install = async () => {
    if (installPrompt) {
      installPrompt.prompt();
      const choice = await installPrompt.userChoice;
      if (choice.outcome === 'accepted') dismiss();
    } else if (isIos) {
      dismiss();
    }
  };

  if (!visible) return null;

  return (
    <div
      className={cn(
        'fixed inset-x-0 z-50 flex items-center justify-between gap-3 border-t bg-card px-4 py-3 shadow-lg sm:px-6',
        position === 'top' ? 'top-0 border-b border-t-0' : 'bottom-0',
        className
      )}
      role="region"
      aria-label="App install banner"
    >
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
          <Smartphone className="h-5 w-5 text-primary" aria-hidden="true" />
        </span>
        <div>
          <p className="text-sm font-semibold text-foreground">{appName}</p>
          <p className="text-xs text-muted-foreground">{description}</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={dismiss}
          aria-label="Dismiss install banner"
          className="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40"
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </button>
        <button
          type="button"
          onClick={install}
          className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-all duration-200 hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/40"
        >
          <Download className="h-4 w-4" aria-hidden="true" />
          {isIos ? 'How to install' : 'Install'}
        </button>
      </div>
    </div>
  );
};

export default PWAInstallBanner;
