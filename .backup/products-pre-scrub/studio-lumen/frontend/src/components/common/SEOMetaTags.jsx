import React, { useEffect } from 'react';

const SEOMetaTags = ({
  title = '',
  description = '',
  canonical = '',
  ogImage = '',
  ogType = 'website',
  schema,
}) => {
  useEffect(() => {
    const setMeta = (attr, key, content) => {
      if (!content) return;
      let el = document.head.querySelector(`meta[${attr}="${key}"]`);
      if (!el) {
        el = document.createElement('meta');
        el.setAttribute(attr, key);
        document.head.appendChild(el);
      }
      el.setAttribute('content', content);
    };

    const linkTag = (href) => {
      if (!href) return;
      let el = document.head.querySelector('link[rel="canonical"]');
      if (!el) {
        el = document.createElement('link');
        el.setAttribute('rel', 'canonical');
        document.head.appendChild(el);
      }
      el.setAttribute('href', href);
    };

    if (title) document.title = title;
    setMeta('name', 'description', description);
    setMeta('property', 'og:title', title);
    setMeta('property', 'og:description', description);
    setMeta('property', 'og:type', ogType);
    setMeta('property', 'og:image', ogImage);
    setMeta('name', 'twitter:card', ogImage ? 'summary_large_image' : 'summary');
    setMeta('name', 'twitter:title', title);
    setMeta('name', 'twitter:description', description);
    linkTag(canonical);

    if (schema) {
      let el = document.head.querySelector('script[data-schema-json]');
      if (!el) {
        el = document.createElement('script');
        el.setAttribute('type', 'application/ld+json');
        el.setAttribute('data-schema-json', '');
        document.head.appendChild(el);
      }
      el.textContent = JSON.stringify(schema);
    }

    return undefined;
  }, [title, description, canonical, ogImage, ogType, schema]);

  return null;
};

export default SEOMetaTags;
