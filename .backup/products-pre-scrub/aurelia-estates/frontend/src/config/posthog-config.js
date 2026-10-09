/**
 * PostHog Analytics + Feature Flags Config
 * Auto-generated for A/B testing & feature flagging
 *
 * Setup: npm install posthog-js
 * Add VITE_POSTHOG_KEY=phc_xxx to .env
 */

export const POSTHOG_CONFIG = {
  apiKey: import.meta.env.VITE_POSTHOG_KEY || '',
  apiHost: import.meta.env.VITE_POSTHOG_HOST || 'https://app.posthog.com',
  options: {
    autocapture: true,
    capture_pageview: true,
    capture_pageleave: true,
    disable_session_recording: false,
    enable_recording_console_log: false,
    bootstrap: {
      featureFlags: {},
    },
  },
};

// Registered experiments for this project
export const REGISTERED_EXPERIMENTS = [
  {
    id: 'hero_headline',
    name: 'Hero Headline Copy',
  },
  {
    id: 'contact_form_cta',
    name: 'Contact Form CTA',
  },
];

// Initialize PostHog
export function initPostHog() {
  if (!POSTHOG_CONFIG.apiKey) return;
  import('posthog-js').then(({ default: posthog }) => {
    posthog.init(POSTHOG_CONFIG.apiKey, POSTHOG_CONFIG.options);
    window.__posthog = posthog;
    console.log('[PostHog] Initialized');
  });
}
