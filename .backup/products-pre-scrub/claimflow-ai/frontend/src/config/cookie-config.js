/**
 * Cookie Configuration
 * Region: SA | Regulations: PECA_PK, GDPR
 * Model: OPT-IN — Consent required before non-essential cookies
 */

export const COOKIE_CONFIG = {
  // Consent model
  requireConsent: true, // true = GDPR/opt-in, false = CCPA/opt-out
  region: 'SA',
  regulations: ['PECA_PK', 'GDPR'],

  // Cookie categories
  categories: {
    essential: {
      id: 'essential',
      name: 'Essential Cookies',
      description: 'Required for the website to function. Cannot be disabled.',
      required: true,
      defaultEnabled: true,
    },
    analytics: {
      id: 'analytics',
      name: 'Analytics Cookies',
      description: 'Help us understand how visitors use our website (e.g. Google Analytics).',
      required: false,
      defaultEnabled: false,
    },
    marketing: {
      id: 'marketing',
      name: 'Marketing Cookies',
      description: 'Used to show you relevant advertising and track ad performance.',
      required: false,
      defaultEnabled: false,
    },
    preferences: {
      id: 'preferences',
      name: 'Preference Cookies',
      description: 'Remember your settings like language and currency.',
      required: false,
      defaultEnabled: true,
    },
  },

  // Storage
  consentCookieName: 'lumicore_consent',
  consentCookieExpiry: 365, // days

  // UI
  showBanner: true,
  position: 'bottom', // 'bottom' | 'top' | 'modal'
  privacyPolicyUrl: '/privacy-policy.html',
  termsOfServiceUrl: '/terms-of-service.html',
  cookiePolicyUrl: '/cookie-policy',
};

/**
 * Check if a cookie category is consented
 * Usage: if (hasConsent('analytics')) { loadGA(); }
 */
export function hasConsent(category) {
  try {
    const stored = JSON.parse(localStorage.getItem(COOKIE_CONFIG.consentCookieName) || '{}');
    if (COOKIE_CONFIG.categories[category]?.required) return true;
    return stored[category] ?? COOKIE_CONFIG.categories[category]?.defaultEnabled ?? false;
  } catch {
    return false;
  }
}

/**
 * Save consent choices
 * Usage: saveConsent({ analytics: true, marketing: false, preferences: true })
 */
export function saveConsent(choices) {
  const consent = {
    essential: true,
    timestamp: new Date().toISOString(),
    ...choices,
  };
  localStorage.setItem(COOKIE_CONFIG.consentCookieName, JSON.stringify(consent));
  window.dispatchEvent(new CustomEvent('cookieConsentUpdated', { detail: consent }));
}
