let lemonLoaded = false;

export function loadLemonSqueezy() {
  if (lemonLoaded || typeof window === 'undefined') return Promise.resolve();

  return new Promise((resolve) => {
    if (document.querySelector('script[src*="lemonsqueezy.com/lemon.js"]')) {
      lemonLoaded = true;
      resolve();
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://assets.lemonsqueezy.com/lemon.js';
    script.async = true;
    script.defer = true;
    script.onload = () => {
      lemonLoaded = true;
      if (window.createLemonSqueezy) {
        window.createLemonSqueezy();
      }
      resolve();
    };
    script.onerror = () => {
      resolve();
    };
    document.head.appendChild(script);
  });
}

export function openLemonSqueezyCheckout({ checkoutUrl, customData = {}, onSuccess, onClose }) {
  if (typeof window === 'undefined') return;

  if (checkoutUrl && window.LemonSqueezy?.Url?.Open) {
    window.LemonSqueezy.Url.Open(checkoutUrl);
    return;
  }

  if (checkoutUrl && checkoutUrl.startsWith('http')) {
    window.open(checkoutUrl, '_blank', 'noopener,noreferrer');
    return;
  }

  window.dispatchEvent(
    new CustomEvent('open-mock-checkout', {
      detail: { customData, onSuccess, onClose },
    })
  );
}
