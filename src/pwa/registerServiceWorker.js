/**
 * Register Service Worker for PWA Offline Support
 */
export const registerServiceWorker = () => {
  if (typeof window !== 'undefined' && 'serviceWorker' in navigator && import.meta.env.PROD) {
    window.addEventListener('load', () => {
      navigator.serviceWorker
        .register('/sw.js')
        .then((registration) => {
          registration.onupdatefound = () => {
            const installingWorker = registration.installing;
            if (installingWorker) {
              installingWorker.onstatechange = () => {
                if (installingWorker.state === 'installed' && navigator.serviceWorker.controller) {
                  // New content available — prompt user to refresh
                }
              };
            }
          };
        })
        .catch(() => {
          // ServiceWorker registration failed — non-critical in development
        });
    });
  }
};
