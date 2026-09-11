/**
 * Analytics — privacy-first, env-driven analytics loader.
 * Providers: 'plausible' (default) or 'google' (GA4).
 * Active only when VITE_ENABLE_ANALYTICS=true AND built for production.
 * GA4 is configured with anonymized IPs and SPA page_view tracking.
 */
import { useEffect } from 'react';

const ENABLED = import.meta.env.VITE_ENABLE_ANALYTICS === 'true';
const PROVIDER = import.meta.env.VITE_ANALYTICS_PROVIDER || 'plausible';
const DOMAIN = import.meta.env.VITE_ANALYTICS_DOMAIN || '';
const SCRIPT_URL = import.meta.env.VITE_ANALYTICS_SCRIPT_URL || 'https://plausible.io/js/script.js';
const GOOGLE_TAG = import.meta.env.VITE_GOOGLE_TAG_ID || '';
const GA_TEMPLATE = 'https://www.googletagmanager.com/gtag/js?id=';

const injectScript = (src, attributes = {}) => {
  if (document.querySelector('script[data-analytics-managed]')) return;
  const script = document.createElement('script');
  script.src = src;
  script.async = true;
  script.defer = true;
  script.setAttribute('data-analytics-managed', 'true');
  Object.entries(attributes).forEach(([key, value]) => {
    if (value) script.setAttribute(key, value);
  });
  document.head.appendChild(script);
};

const trackPage = () => {
  if (typeof window.gtag !== 'function') return;
  window.gtag('event', 'page_view', { page_path: window.location.pathname });
};

const installPlausible = () => {
  window.plausible =
    window.plausible ||
    function plausible() {
      (window.plausible.q = window.plausible.q || []).push(arguments);
    };
  injectScript(SCRIPT_URL, DOMAIN ? { 'data-domain': DOMAIN } : {});
};

const installGoogleAnalytics = () => {
  window.dataLayer = window.dataLayer || [];
  window.gtag =
    window.gtag ||
    function gtag() {
      window.dataLayer.push(arguments);
    };
  window.gtag('js', new Date());
  window.gtag('config', GOOGLE_TAG, { anonymize_ip: true, send_page_view: true });
  injectScript(`${GA_TEMPLATE}${GOOGLE_TAG}`);

  trackPage();
  const nativePushState = window.history.pushState;
  window.history.pushState = function pushState(...args) {
    nativePushState.apply(window.history, args);
    trackPage();
  };
  window.addEventListener('popstate', trackPage);
};

/**
 * Analytics root component — mounts once, injects nothing when disabled.
 */
export default function Analytics() {
  useEffect(() => {
    if (!ENABLED || !import.meta.env.PROD) return;

    if (PROVIDER === 'google' && GOOGLE_TAG) {
      installGoogleAnalytics();
    } else if (PROVIDER === 'plausible') {
      installPlausible();
    }
  }, []);

  return null;
}
