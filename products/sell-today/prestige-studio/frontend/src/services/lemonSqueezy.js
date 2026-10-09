/**
 * Lemon Squeezy storefront helper
 * ------------------------------
 * Resolution order for a checkout:
 *   1. an explicit checkout URL passed by the caller
 *   2. the store overlay link (VITE_LEMONSQUEEZY_STORE_URL + variant id)
 *   3. the backend checkout endpoint (authoritative, records the order)
 *   4. the built-in demo dialog, so the pricing page still works before keys
 *      are inserted
 */
const LEMON_SCRIPT = 'https://assets.lemonsqueezy.com/lemon.js';

const env = (key, fallback = '') =>
  (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env[key]) || fallback;

export const lemonSqueezyConfig = {
  storeId: env('VITE_LEMONSQUEEZY_STORE_ID'),
  storeUrl: env('VITE_LEMONSQUEEZY_STORE_URL').replace(/\/+$/, ''),
  variantId: env('VITE_LEMONSQUEEZY_VARIANT_ID'),
  apiBase: env('VITE_API_URL').replace(/\/+$/, ''),
};

let lemonLoaded = false;

/** Loads the Lemon Squeezy overlay script once per session. */
export function loadLemonSqueezy() {
  if (lemonLoaded || typeof window === 'undefined') return Promise.resolve();

  return new Promise((resolve) => {
    if (document.querySelector('script[src*="lemonsqueezy.com/lemon.js"]')) {
      lemonLoaded = true;
      resolve();
      return;
    }

    const script = document.createElement('script');
    script.src = LEMON_SCRIPT;
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

const openUrl = (url) => {
  if (!url || typeof window === 'undefined') return false;
  if (window.LemonSqueezy?.Url?.Open) {
    window.LemonSqueezy.Url.Open(url);
    return true;
  }
  window.open(url, '_blank', 'noopener,noreferrer');
  return true;
};

/** Store configuration served by the API — probed once, never cached on failure. */
export async function getStoreConfig() {
  if (!lemonSqueezyConfig.apiBase) return null;
  try {
    const response = await fetch(`${lemonSqueezyConfig.apiBase}/api/lemonsqueezy/config`, {
      headers: { Accept: 'application/json' },
    });
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

/** Ask the backend for a hosted checkout URL. */
async function requestCheckout(payload) {
  if (!lemonSqueezyConfig.apiBase) return null;
  try {
    const response = await fetch(`${lemonSqueezyConfig.apiBase}/api/lemonsqueezy/checkout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) return null;
    const body = await response.json();
    return body?.url ? body : null;
  } catch {
    return null;
  }
}

const overlayUrl = (variantId) => {
  if (!lemonSqueezyConfig.storeUrl || !variantId) return '';
  return `${lemonSqueezyConfig.storeUrl}/buy/variant:${variantId}`;
};

/**
 * Demo fallback: a small self-contained dialog. It never charges anyone and it
 * makes the difference between "not configured yet" and a broken page obvious.
 */
function openDemoCheckout({ planName, price, onSuccess }) {
  if (typeof document === 'undefined') return;

  const existing = document.getElementById('lemon-squeezy-demo');
  if (existing) existing.remove();

  const overlay = document.createElement('div');
  overlay.id = 'lemon-squeezy-demo';
  overlay.setAttribute('role', 'dialog');
  overlay.setAttribute('aria-modal', 'true');
  overlay.setAttribute('aria-label', 'Checkout preview');
  overlay.style.cssText =
    'position:fixed;inset:0;z-index:9999;display:flex;align-items:center;justify-content:center;padding:24px;background:rgba(2,6,23,.82);backdrop-filter:blur(6px);';
  overlay.innerHTML = `
    <div style="max-width:420px;width:100%;border-radius:20px;border:1px solid rgba(148,163,184,.25);background:#0b1220;padding:28px;font-family:inherit;color:#e2e8f0;box-shadow:0 30px 60px rgba(0,0,0,.45)">
      <h3 style="margin:0 0 6px;font-size:18px;font-weight:700;color:#fff">Checkout preview</h3>
      <p style="margin:0 0 16px;font-size:13px;line-height:1.6;color:#94a3b8">
        ${planName ? `<strong style="color:#e2e8f0">${planName}</strong>${price ? ` — $${price}` : ''}.<br/>` : ''}
        This storefront has no Lemon Squeezy keys yet, so no payment is taken. Add the store
        details from <code>frontend/.env</code> to switch this button to real checkout.
      </p>
      <button type="button" id="lemon-squeezy-demo-close"
        style="width:100%;padding:11px 16px;border-radius:12px;border:0;background:linear-gradient(90deg,#22d3ee,#2563eb);color:#fff;font-size:13px;font-weight:700;cursor:pointer">
        Got it
      </button>
    </div>`;

  const close = () => {
    overlay.remove();
    if (typeof onSuccess === 'function') onSuccess({ demo: true });
  };
  overlay.querySelector('#lemon-squeezy-demo-close').addEventListener('click', close);
  overlay.addEventListener('click', (event) => {
    if (event.target === overlay) close();
  });
  document.body.appendChild(overlay);

  // Kept for integrations that listen for the event instead of the dialog.
  window.dispatchEvent(
    new CustomEvent('open-mock-checkout', {
      detail: { customData: { planName, price } },
    })
  );
}

/**
 * Open checkout for a plan.
 * Pass `checkoutUrl` to bypass resolution, `variantId` to pin a variant, or
 * `customData` (the pricing table passes planName/amount/billingCycle).
 */
export async function openLemonSqueezyCheckout({
  checkoutUrl,
  variantId,
  customData = {},
  onSuccess,
  onClose,
} = {}) {
  if (typeof window === 'undefined') return;

  const planName = customData.planName || customData.plan || '';

  if (checkoutUrl && openUrl(checkoutUrl)) return;

  await loadLemonSqueezy();

  const variant = variantId || lemonSqueezyConfig.variantId || '';
  const overlay = overlayUrl(variant);
  if (overlay && openUrl(overlay)) return;

  const remote = await requestCheckout({ ...customData, planName, variantId: variant || undefined });
  if (remote && openUrl(remote.url)) return;

  openDemoCheckout({ planName, price: customData.amount, onSuccess, onClose });
}

export default { loadLemonSqueezy, openLemonSqueezyCheckout, getStoreConfig, lemonSqueezyConfig };
