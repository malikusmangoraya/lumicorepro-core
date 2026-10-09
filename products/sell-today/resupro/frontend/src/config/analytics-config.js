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
    posthogHost: import.meta.env.VITE_POSTHOG_HOST || 'https://malikusmangoraya.github.io/resupro',
    // Plausible (privacy-first)
    plausibleDomain: import.meta.env.VITE_PLAUSIBLE_DOMAIN || '',
    plausibleApiHost: import.meta.env.VITE_PLAUSIBLE_HOST || 'https://malikusmangoraya.github.io/resupro',
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
  view_item_list: 'Products page load',
  view_item: 'Product detail page load',
  add_to_cart: 'Add to cart button click',
  remove_from_cart: 'Remove from cart',
  view_cart: 'Cart page view',
  begin_checkout: 'Checkout step 1',
  add_payment_info: 'Payment info entered',
  purchase: 'Order confirmed',
  refund: 'Refund processed',
  add_to_wishlist: 'Wishlist button click',
  search: 'Search submitted',
  select_promotion: 'Banner/promo click',
  sign_up: 'Account created',
  login: 'User logged in',
};
