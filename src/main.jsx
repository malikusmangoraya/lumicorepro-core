import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.jsx';
import { registerServiceWorker } from './pwa/registerServiceWorker';
import { initSentry } from './utils/sentry';

// Error tracking first: captures anything thrown during boot. Lazy-loads
// the Sentry SDK only when VITE_SENTRY_DSN is set (see utils/sentry.js);
// a failed fetch is non-fatal, so the rejection is deliberately swallowed.
initSentry().catch(() => {});

// Register PWA service worker
registerServiceWorker();

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>
);
