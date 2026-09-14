import { useEffect } from 'react';
import i18n from '@/i18n';

/* ── Site-wide SEO config (env-driven) ──────────────────────────────────── */
const SITE_URL = (import.meta.env.VITE_SITE_URL || 'https://lumicorepro.com').replace(/\/$/, '');
const SITE_NAME = import.meta.env.VITE_APP_NAME || 'LumiCorePro';
const TWITTER_HANDLE = import.meta.env.VITE_TWITTER_HANDLE || '@lumicorepro';
const OG_IMAGE = import.meta.env.VITE_DEFAULT_OG_IMAGE || `${SITE_URL}/lumicorepro-brand-logo.png`;

/* ── Language → OpenGraph locale mapping ───────────────────────────────── */
export const seoLocales = {
  en: 'en_US',
  es: 'es_ES',
  fr: 'fr_FR',
  de: 'de_DE',
  it: 'it_IT',
  pt: 'pt_PT',
  ar: 'ar_SA',
  ur: 'ur_PK',
  zh: 'zh_CN',
  ja: 'ja_JP',
  ko: 'ko_KR',
  hi: 'hi_IN',
  tr: 'tr_TR',
};

/**
 * Build hreflang alternates for every supported language using path prefixes.
 * English stays at the bare path; other languages use `/{lang}{path}`.
 * @param {string} pathname — local path, e.g. '/templates' or '/'
 * @param {string} origin   — absolute site origin, e.g. 'https://lumicorepro.com'
 */
export const hreflangFor = (pathname = '/', origin = '') => {
  const path = pathname.startsWith('/') && pathname !== '/' ? pathname : '';
  return Object.fromEntries(
    Object.keys(seoLocales).map((lang) => [
      lang,
      `${origin}${lang === 'en' ? path || '/' : `/${lang}${path || ''}`}`,
    ])
  );
};

/* ── Schema.org JSON-LD Generators ─────────────────────────────────────────
 * Usage:
 *   import SEO, { schemas } from '@/components/common/SEO';
 *
 *   // Single schema
 *   <SEO title="..." schema={schemas.organization({ name: 'Acme', url: '...' })} />
 *
 *   // Multiple schemas
 *   <SEO schema={[schemas.organization({...}), schemas.website({...})]} />
 * ─────────────────────────────────────────────────────────────────────── */
export const schemas = {
  /** Generic organization / brand */
  organization: ({ name, url, logo, description, sameAs = [] }) => ({
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name,
    url,
    logo: logo ? { '@type': 'ImageObject', url: logo } : undefined,
    description,
    sameAs,
  }),

  /** Website / sitelinks searchbox */
  website: ({ name, url, searchUrl }) => ({
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name,
    url,
    ...(searchUrl && {
      potentialAction: {
        '@type': 'SearchAction',
        target: { '@type': 'EntryPoint', urlTemplate: `${searchUrl}?q={search_term_string}` },
        'query-input': 'required name=search_term_string',
      },
    }),
  }),

  /** Web page */
  webPage: ({ name, url, description, breadcrumb }) => ({
    '@context': 'https://schema.org',
    '@type': 'WebPage',
    name,
    url,
    description,
    ...(breadcrumb && { breadcrumb }),
  }),

  /** Product listing / e-commerce product */
  product: ({
    name,
    description,
    image,
    sku,
    brand,
    price,
    currency = 'USD',
    availability = 'InStock',
    rating,
    reviewCount,
  }) => ({
    '@context': 'https://schema.org',
    '@type': 'Product',
    name,
    description,
    image,
    sku,
    brand: brand ? { '@type': 'Brand', name: brand } : undefined,
    offers: {
      '@type': 'Offer',
      price,
      priceCurrency: currency,
      availability: `https://schema.org/${availability}`,
      url: typeof window !== 'undefined' ? window.location.href : '',
    },
    ...(rating && {
      aggregateRating: {
        '@type': 'AggregateRating',
        ratingValue: rating,
        reviewCount: reviewCount || 1,
      },
    }),
  }),

  /** Blog article / news article */
  article: ({
    headline,
    description,
    image,
    datePublished,
    dateModified,
    authorName,
    publisherName,
    publisherLogo,
    url,
  }) => ({
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline,
    description,
    image,
    datePublished,
    dateModified: dateModified || datePublished,
    author: { '@type': 'Person', name: authorName },
    publisher: {
      '@type': 'Organization',
      name: publisherName,
      logo: publisherLogo ? { '@type': 'ImageObject', url: publisherLogo } : undefined,
    },
    url,
  }),

  /** Local business (restaurant, clinic, gym, etc.) */
  localBusiness: ({
    name,
    type = 'LocalBusiness',
    url,
    telephone,
    address,
    geo,
    openingHours = [],
    image,
    priceRange,
  }) => ({
    '@context': 'https://schema.org',
    '@type': type,
    name,
    url,
    telephone,
    image,
    priceRange,
    address: {
      '@type': 'PostalAddress',
      ...address,
    },
    ...(geo && {
      geo: { '@type': 'GeoCoordinates', latitude: geo.lat, longitude: geo.lng },
    }),
    ...(openingHours.length && { openingHours }),
  }),

  /** Restaurant */
  restaurant: (props) => schemas.localBusiness({ ...props, type: 'Restaurant' }),

  /** Medical clinic / doctor */
  medicalBusiness: ({ name, url, telephone, address, medicalSpecialty }) => ({
    '@context': 'https://schema.org',
    '@type': 'MedicalBusiness',
    name,
    url,
    telephone,
    medicalSpecialty,
    address: { '@type': 'PostalAddress', ...address },
  }),

  /** Real estate listing */
  realEstateListing: ({ name, description, url, price, currency = 'USD', address }) => ({
    '@context': 'https://schema.org',
    '@type': 'RealEstateListing',
    name,
    description,
    url,
    offers: { '@type': 'Offer', price, priceCurrency: currency },
    address: { '@type': 'PostalAddress', ...address },
  }),

  /** Course / educational offering */
  course: ({ name, description, provider, url, price, currency = 'USD' }) => ({
    '@context': 'https://schema.org',
    '@type': 'Course',
    name,
    description,
    url,
    provider: { '@type': 'Organization', name: provider },
    ...(price !== undefined && {
      offers: { '@type': 'Offer', price, priceCurrency: currency },
    }),
  }),

  /** Event (conference, webinar, meetup) */
  event: ({
    name,
    description,
    startDate,
    endDate,
    location,
    url,
    organizer,
    isOnline = false,
    image,
  }) => ({
    '@context': 'https://schema.org',
    '@type': 'Event',
    name,
    description,
    startDate,
    endDate,
    url,
    image,
    eventAttendanceMode: isOnline
      ? 'https://schema.org/OnlineEventAttendanceMode'
      : 'https://schema.org/OfflineEventAttendanceMode',
    location: isOnline
      ? { '@type': 'VirtualLocation', url }
      : {
          '@type': 'Place',
          name: location?.name,
          address: { '@type': 'PostalAddress', ...location },
        },
    organizer: organizer ? { '@type': 'Organization', name: organizer } : undefined,
  }),

  /** SaaS / software application */
  softwareApp: ({
    name,
    description,
    url,
    price = '0.00',
    currency = 'USD',
    os = 'All',
    category = 'BusinessApplication',
  }) => ({
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name,
    description,
    url,
    applicationCategory: category,
    operatingSystem: os,
    offers: { '@type': 'Offer', price, priceCurrency: currency },
  }),

  /** Person / personal portfolio */
  person: ({ name, url, jobTitle, description, image, sameAs = [] }) => ({
    '@context': 'https://schema.org',
    '@type': 'Person',
    name,
    url,
    jobTitle,
    description,
    image,
    sameAs,
  }),

  /** FAQ page */
  faq: (items = []) => ({
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: items.map(({ question, answer }) => ({
      '@type': 'Question',
      name: question,
      acceptedAnswer: { '@type': 'Answer', text: answer },
    })),
  }),

  /** Breadcrumb list */
  breadcrumb: (items = []) => ({
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map(({ name, url }, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name,
      item: url,
    })),
  }),

  /** Review / aggregate rating */
  review: ({ itemName, ratingValue, reviewCount, bestRating = 5 }) => ({
    '@context': 'https://schema.org',
    '@type': 'Review',
    itemReviewed: { '@type': 'Thing', name: itemName },
    reviewRating: {
      '@type': 'Rating',
      ratingValue,
      bestRating,
    },
    aggregateRating: {
      '@type': 'AggregateRating',
      ratingValue,
      reviewCount,
      bestRating,
    },
  }),
};

/* ── SEO Component ──────────────────────────────────────────────────────── */
/**
 * SEO — Dynamic document head manager with full JSON-LD structured data
 *
 * @param {string}  title         — Page <title>
 * @param {string}  description   — Meta description
 * @param {string}  keywords      — Meta keywords
 * @param {string}  ogImage       — Open Graph image URL
 * @param {string}  ogType        — OG type: 'website' | 'article' | 'product'
 * @param {string}  canonicalUrl  — Canonical URL (defaults to current href)
 * @param {string}  locale        — Locale for og:locale (default 'en_US')
 * @param {string}  twitterSite   — Twitter @handle for twitter:site
 * @param {boolean} noIndex       — Set robots noindex,nofollow
 * @param {object|object[]} schema — JSON-LD schema object or array of schemas
 * @param {object}  hreflang      — hreflang alternates { 'ar': 'https://...', 'ur': 'https://...' }
 * @param {string}  defaultLanguage — Default language code (e.g., 'en')
 */
const SEO = ({
  title = 'LumiCorePro — Full-Stack Enterprise Platform & AI Studio',
  description = 'Build, launch, and scale modern web applications with 60+ responsive templates, AI agents, e-commerce, and real-time backend.',
  keywords = 'react, fullstack, ecommerce, ai studio, dashboard, tailwindcss, nodejs, express, mongodb',
  ogImage = OG_IMAGE,
  ogType = 'website',
  canonicalUrl,
  locale,
  twitterSite = TWITTER_HANDLE,
  noIndex = false,
  schema = null,
  hreflang = null,
  defaultLanguage = 'en',
}) => {
  const resolvedUrl = canonicalUrl || (typeof window !== 'undefined' ? window.location.href : '');
  const resolvedLocale =
    locale || seoLocales[i18n.language] || seoLocales[i18n.languages?.[0]] || 'en_US';

  useEffect(() => {
    /* ── 1. Title ─────────────────────────────────────────────── */
    document.title = title;

    /* ── 2. Meta tag helper ───────────────────────────────────── */
    const setMeta = (attr, val, content) => {
      let el = document.querySelector(`meta[${attr}="${val}"]`);
      if (!el) {
        el = document.createElement('meta');
        el.setAttribute(attr, val);
        document.head.appendChild(el);
      }
      el.setAttribute('content', content ?? '');
    };

    /* ── 3. Standard meta ─────────────────────────────────────── */
    setMeta('name', 'description', description);
    setMeta('name', 'keywords', keywords);
    setMeta('name', 'robots', noIndex ? 'noindex,nofollow' : 'index,follow');
    setMeta('name', 'theme-color', 'var(--t-primary)');
    setMeta('name', 'viewport', 'width=device-width, initial-scale=1');

    /* ── 4. Open Graph ────────────────────────────────────────── */
    setMeta('property', 'og:title', title);
    setMeta('property', 'og:description', description);
    setMeta('property', 'og:image', ogImage);
    setMeta('property', 'og:image:width', '1200');
    setMeta('property', 'og:image:height', '630');
    setMeta('property', 'og:type', ogType);
    setMeta('property', 'og:url', resolvedUrl);
    setMeta('property', 'og:locale', resolvedLocale);
    setMeta('property', 'og:site_name', SITE_NAME);

    /* ── 4b. OG locale alternates (all non-active languages) ───── */
    document.querySelectorAll('meta[property="og:locale:alternate"]').forEach((el) => el.remove());
    Object.values(seoLocales)
      .filter((l) => l !== resolvedLocale)
      .forEach((l) => setMeta('property', 'og:locale:alternate', l));

    /* ── 5. Twitter Card ──────────────────────────────────────── */
    setMeta('name', 'twitter:card', 'summary_large_image');
    setMeta('name', 'twitter:site', twitterSite);
    setMeta('name', 'twitter:title', title);
    setMeta('name', 'twitter:description', description);
    setMeta('name', 'twitter:image', ogImage);

    /* ── 6. Canonical ─────────────────────────────────────────── */
    let canonical = document.querySelector('link[rel="canonical"]');
    if (!canonical) {
      canonical = document.createElement('link');
      canonical.setAttribute('rel', 'canonical');
      document.head.appendChild(canonical);
    }
    canonical.setAttribute('href', resolvedUrl);

    /* ── 6b. hreflang Alternates (Multi-language SEO) ──────────── */
    // Remove all previous hreflang links
    document.querySelectorAll('link[rel="alternate"][hreflang]').forEach((l) => l.remove());

    // Add hreflang links if provided
    if (hreflang && typeof hreflang === 'object') {
      Object.entries(hreflang).forEach(([lang, url]) => {
        const link = document.createElement('link');
        link.setAttribute('rel', 'alternate');
        link.setAttribute('hreflang', lang);
        link.setAttribute('href', url);
        document.head.appendChild(link);
      });

      // Add x-default hreflang pointing to default language version
      const xDefaultLink = document.createElement('link');
      xDefaultLink.setAttribute('rel', 'alternate');
      xDefaultLink.setAttribute('hreflang', 'x-default');
      xDefaultLink.setAttribute('href', resolvedUrl);
      document.head.appendChild(xDefaultLink);
    }

    /* ── 7. JSON-LD Structured Data ──────────────────────────── */
    // Remove all previous schema scripts
    document.querySelectorAll('script[data-lumicore-schema]').forEach((s) => s.remove());

    const schemaArray = Array.isArray(schema)
      ? schema
      : schema
        ? [schema]
        : [
            {
              '@context': 'https://schema.org',
              '@type': 'SoftwareApplication',
              name: 'LumiCorePro',
              applicationCategory: 'BusinessApplication',
              operatingSystem: 'All',
              offers: { '@type': 'Offer', price: '0.00', priceCurrency: 'USD' },
              description,
              url: resolvedUrl,
            },
          ];

    schemaArray.forEach((s, i) => {
      const script = document.createElement('script');
      script.type = 'application/ld+json';
      script.setAttribute('data-lumicore-schema', String(i));
      script.textContent = JSON.stringify(s, null, 0);
      document.head.appendChild(script);
    });
  }, [
    title,
    description,
    keywords,
    ogImage,
    ogType,
    resolvedUrl,
    resolvedLocale,
    twitterSite,
    noIndex,
    schema,
    hreflang,
  ]);

  return null;
};

export default SEO;
