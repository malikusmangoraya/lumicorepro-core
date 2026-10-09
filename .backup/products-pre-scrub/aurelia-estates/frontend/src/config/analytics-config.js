/**
 * Analytics Configuration
 * Primary: ga4 | Secondary: posthog
 */

export const ANALYTICS_CONFIG = {
  primary: {
    provider: 'ga4',
    // GA4
    ga4MeasurementId: import.meta.env.VITE_GA4_ID || '',
    // PostHog
    posthogKey: import.meta.env.VITE_POSTHOG_KEY || '',
    posthogHost: import.meta.env.VITE_POSTHOG_HOST || 'https://app.posthog.com',
    // Plausible (privacy-first)
    plausibleDomain: import.meta.env.VITE_PLAUSIBLE_DOMAIN || '',
    plausibleApiHost: import.meta.env.VITE_PLAUSIBLE_HOST || 'https://plausible.io',
    // Mixpanel
    mixpanelToken: import.meta.env.VITE_MIXPANEL_TOKEN || '',
    // Fathom (cookie-free)
    fathomSiteId: import.meta.env.VITE_FATHOM_SITE_ID || '',
  },
  options: {
    debug: import.meta.env.DEV,
    respectDoNotTrack: true,
    cookieless: false,
    sampleRate: 1.0, // 100% of users
  },
};

// Event name registry
export const EVENTS = {
  page_view: 'Page load',
  scroll: '25/50/75/90% scroll depth',
  click: 'Link/button click',
  search: 'Site search',
  contact_submitted: 'Contact form submitted',
  sign_up: 'Newsletter/account signup',
  share: 'Social share button click',
};
