import SEO, { hreflangFor } from './SEO';

/**
 * PageSEO — Drop-in SEO wrapper that auto-emits hreflang alternates for all
 * supported languages on every page. Use on any marketing/page route.
 *
 * @param {string} title       — <title> text
 * @param {string} description — meta description
 * @param {string} keywords    — meta keywords
 * @param {string} canonicalUrl — absolute canonical URL (defaults to current href)
 * @param {object|object[]} schema — JSON-LD schema(s)
 * @param {boolean} noIndex    — robots noindex (auth/admin pages)
 */
const PageSEO = ({ title, description, keywords, canonicalUrl, schema, noIndex = false }) => {
  const origin = typeof window !== 'undefined' ? window.location.origin : '';
  const path = typeof window !== 'undefined' ? window.location.pathname : '/';

  return (
    <SEO
      title={title}
      description={description}
      keywords={keywords}
      canonicalUrl={canonicalUrl}
      schema={schema}
      noIndex={noIndex}
      hreflang={origin ? hreflangFor(path, origin) : null}
    />
  );
};

export default PageSEO;