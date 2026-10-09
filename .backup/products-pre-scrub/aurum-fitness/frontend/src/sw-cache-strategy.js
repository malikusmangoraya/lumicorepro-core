/**
 * Service Worker Cache Strategy
 */

export const CACHE_STRATEGIES = {
  html: {
    strategy: 'network-first',
    maxAge: 0,
    desc: 'Always fresh HTML',
  },
  css: {
    strategy: 'cache-first',
    maxAge: 31536000,
    desc: '1 year \u2014 hash in filename',
  },
  js: {
    strategy: 'cache-first',
    maxAge: 31536000,
    desc: '1 year \u2014 hash in filename',
  },
  images: {
    strategy: 'cache-first',
    maxAge: 2592000,
    desc: '30 days',
  },
  fonts: {
    strategy: 'cache-first',
    maxAge: 31536000,
    desc: '1 year',
  },
  api: {
    strategy: 'network-first',
    maxAge: 300,
    desc: '5 min stale-while-revalidate',
  },
  static: {
    strategy: 'cache-first',
    maxAge: 86400,
    desc: '24 hours',
  },
};

export const CACHE_NAME = 'lumicore-v1';
export const OFFLINE_URL = '/offline.html';

/**
 * Get cache strategy for a given request URL
 */
export function getStrategy(url) {
  if (url.includes('/api/')) return CACHE_STRATEGIES.api;
  if (url.match(/\.html$/)) return CACHE_STRATEGIES.html;
  if (url.match(/\.css$/)) return CACHE_STRATEGIES.css;
  if (url.match(/\.(js|mjs)$/)) return CACHE_STRATEGIES.js;
  if (url.match(/\.(png|jpg|jpeg|webp|avif|gif|svg)$/)) return CACHE_STRATEGIES.images;
  if (url.match(/\.(woff2?|ttf|eot)$/)) return CACHE_STRATEGIES.fonts;
  return CACHE_STRATEGIES.static;
}
