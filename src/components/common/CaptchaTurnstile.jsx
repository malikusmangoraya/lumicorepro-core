import { useRef, useEffect, useState, useCallback } from 'react';

/**
 * Cloudflare Turnstile widget wrapper (FREE, no dependency lib).
 * Loads the official Cloudflare script on demand and renders the checkbox.
 * Exposes the verified token via `onVerify(token)`.
 *
 * Props:
 *  - siteKey: your Turnstile site key (public)
 *  - onVerify: (token: string | null) => void
 *  - theme: 'light' | 'dark' | 'auto'
 *  - size: 'normal' | 'compact'
 */
const SCRIPT_SRC = 'https://challenges.cloudflare.com/turnstile/v0/api.js';

let scriptPromise = null;

function loadTurnstileScript() {
  if (window.turnstile) return Promise.resolve(window.turnstile);
  if (scriptPromise) return scriptPromise;

  scriptPromise = new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${SCRIPT_SRC}"]`);
    if (existing) {
      existing.addEventListener('load', () => resolve(window.turnstile));
      existing.addEventListener('error', () => reject(new Error('Turnstile script failed to load')));
      return;
    }
    const script = document.createElement('script');
    script.src = SCRIPT_SRC;
    script.async = true;
    script.defer = true;
    script.onload = () => resolve(window.turnstile);
    script.onerror = () => {
      scriptPromise = null;
      reject(new Error('Turnstile script failed to load'));
    };
    document.head.appendChild(script);
  });

  return scriptPromise;
}

export default function Turnstile({ siteKey, onVerify, theme = 'dark', size = 'normal' }) {
  const containerRef = useRef(null);
  const widgetIdRef = useRef(null);
  const [status, setStatus] = useState('idle'); // idle | loading | ready | error
  const [error, setError] = useState('');
  const onVerifyRef = useRef(onVerify);

  useEffect(() => {
    onVerifyRef.current = onVerify;
  }, [onVerify]);

  const renderWidget = useCallback(() => {
    if (!window.turnstile || !containerRef.current) return;
    try {
      setStatus('ready');
      widgetIdRef.current = window.turnstile.render(containerRef.current, {
        sitekey: siteKey,
        theme,
        size,
        callback: (token) => onVerifyRef.current?.(token),
        'expired-callback': () => onVerifyRef.current?.(null),
        'error-callback': () => {
          onVerifyRef.current?.(null);
          setError('Captcha failed. Please try again.');
        },
      });
    } catch (err) {
      setStatus('error');
      setError('Could not initialize captcha.');
    }
  }, [siteKey, theme, size]);

  useEffect(() => {
    if (!siteKey) {
      setStatus('error');
      setError('Captcha site key not configured.');
      return;
    }
    setStatus('loading');
    loadTurnstileScript()
      .then(renderWidget)
      .catch(() => {
        setStatus('error');
        setError('Captcha could not load. Check your connection.');
      });
    return () => {
      if (window.turnstile && widgetIdRef.current) {
        try {
          window.turnstile.remove(widgetIdRef.current);
        } catch {
          /* ignore */
        }
      }
    };
  }, [siteKey, renderWidget]);

  return (
    <div className="captcha-wrap">
      <div ref={containerRef} className="flex min-h-[70px] flex-col justify-center" />
      {status === 'loading' && (
        <p className="text-xs text-muted-foreground">Loading security check…</p>
      )}
      {status === 'error' && error && (
        <p className="text-xs text-destructive" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}