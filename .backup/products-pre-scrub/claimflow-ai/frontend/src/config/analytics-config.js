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
  sign_up: 'Account created',
  login: 'User logged in',
  trial_started: 'Free trial started',
  trial_converted: 'Trial \u2192 paid conversion',
  plan_selected: 'Pricing page plan click',
  subscription_created: 'Subscription confirmed',
  subscription_cancelled: 'Cancellation confirmed',
  feature_used: 'Key feature interaction',
  onboarding_step: 'Onboarding step completed',
  onboarding_completed: 'Full onboarding done',
  invite_sent: 'Team member invited',
  search: 'In-app search',
};
