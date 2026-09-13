/**
 * Website Layout Kit & Blueprint Architecture
 * Standardized high-converting layout combinations for modern market demand.
 */

export const LAYOUT_PRESETS = {
  saas: {
    name: 'Modern SaaS / AI Platform',
    navigation: {
      type: 'floating-glass',
      features: ['brand-logo', 'mega-menu', 'search-cmd-k', 'theme-toggle', 'cta-glow'],
    },
    sections: [
      { type: 'hero-bento', name: 'Hero with 3D Cyber Particle & Bento Showcase' },
      { type: 'social-proof-marquee', name: 'Infinite Logo & Trust Metrics Marquee' },
      { type: 'spotlight-features', name: 'Interactive Spotlight Grid Feature Cards' },
      { type: 'holographic-showcase', name: '3D Holographic Perspective UI Preview' },
      { type: 'tabbed-workflows', name: 'Animated Tabbed Workflow Switcher' },
      { type: 'pricing-matrix', name: 'Tiered Pricing with Toggle & Popular Badge' },
      { type: 'faq-accordion', name: 'Interactive Smooth Accordion FAQ' },
      { type: 'cta-banner', name: 'Glowing Gradient Border CTA Banner' },
    ],
    footer: {
      type: 'pro-multi-column',
      columns: 5,
      features: ['status-badge', 'newsletter-box', 'social-dock', 'legal-matrix'],
    },
  },

  ecommerce: {
    name: 'Modern E-Commerce Storefront',
    navigation: {
      type: 'sticky-glass',
      features: ['brand-logo', 'category-drawer', 'search-live', 'cart-badge', 'currency-switcher'],
    },
    sections: [
      { type: 'hero-slider', name: 'Hero Banner with Seasonal Highlight & Quick CTAs' },
      { type: 'category-pills', name: 'Horizontal Scroll Category Carousel' },
      { type: 'bento-featured', name: 'Bento Grid Trending Products with Quick View' },
      { type: 'spotlight-deals', name: 'Flash Deals with Animated Countdown Timers' },
      { type: 'reviews-masonry', name: 'Customer Testimonial & Photo Grid' },
      { type: 'trust-perks', name: 'Free Shipping, 30-Day Returns, 24/7 Support Badges' },
    ],
    footer: {
      type: 'pro-multi-column',
      columns: 5,
      features: ['payment-badges', 'newsletter-discount', 'order-tracking-link'],
    },
  },

  fintech: {
    name: 'Fintech & Digital Banking',
    navigation: {
      type: 'minimal-dock',
      features: ['brand-logo', 'security-badge', 'live-market-ticker', 'login-btn'],
    },
    sections: [
      { type: 'hero-hologram', name: 'Hero with 3D Card Simulation & Yield Calculator' },
      { type: 'security-matrix', name: 'Bank-Grade AES-256 Encryption & SOC2 Trust Grid' },
      { type: 'bento-metrics', name: 'Realtime Analytics & Asset Allocation Bento Grid' },
      { type: 'comparison-table', name: 'Interactive Fee & Performance Comparison Table' },
      { type: 'cta-glow', name: 'Instant Account Opening with Biometric Verification' },
    ],
    footer: {
      type: 'pro-multi-column',
      columns: 5,
      features: ['regulatory-disclosures', 'fdic-badge', 'status-badge'],
    },
  },

  creative: {
    name: 'Creative Studio / Agency / Portfolio',
    navigation: {
      type: 'floating-pill',
      features: ['brand-logo', 'work-links', 'contact-trigger', 'magnetic-cta'],
    },
    sections: [
      { type: 'hero-text-morph', name: 'Huge Typography with TextMorph & Glitch FX' },
      { type: 'work-bento', name: 'Interactive Project Case Studies with Parallax Tilt' },
      { type: 'services-spotlight', name: 'Service Capabilities with Spotlight Hover' },
      { type: 'awards-ticker', name: 'Infinite Marquee of Design Awards & Clients' },
      { type: 'magnetic-contact', name: 'Direct Inquiry Form with Magnetic Submit' },
    ],
    footer: {
      type: 'pro-multi-column',
      columns: 4,
      features: ['big-email-cta', 'social-matrix', 'local-time-clock'],
    },
  },
};

export function getRecommendedLayout(industry = 'saas') {
  const normalized = industry.toLowerCase();
  if (normalized.includes('shop') || normalized.includes('store') || normalized.includes('ecom')) {
    return LAYOUT_PRESETS.ecommerce;
  }
  if (normalized.includes('bank') || normalized.includes('crypto') || normalized.includes('fin')) {
    return LAYOUT_PRESETS.fintech;
  }
  if (normalized.includes('design') || normalized.includes('agency') || normalized.includes('portfolio')) {
    return LAYOUT_PRESETS.creative;
  }
  return LAYOUT_PRESETS.saas;
}

export default LAYOUT_PRESETS;
