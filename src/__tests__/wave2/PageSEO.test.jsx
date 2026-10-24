import { describe, expect, it } from 'vitest';
import { render } from '@testing-library/react';
import PageSEO from '../../components/common/PageSEO';

const meta = (attr, value) =>
  document.querySelector(`meta[${attr}="${value}"]`)?.getAttribute('content');

const alternateLinks = () =>
  [...document.querySelectorAll('link[rel="alternate"][hreflang]')];

describe('PageSEO', () => {
  it('writes the title, description, keywords and indexable robots meta', () => {
    render(
      <PageSEO
        title="Pricing — LumicorePro"
        description="Transparent plans for every team."
        keywords="pricing, plans, saas"
      />
    );

    expect(document.title).toBe('Pricing — LumicorePro');
    expect(meta('name', 'description')).toBe('Transparent plans for every team.');
    expect(meta('name', 'keywords')).toBe('pricing, plans, saas');
    expect(meta('name', 'robots')).toBe('index,follow');
    expect(meta('property', 'og:title')).toBe('Pricing — LumicorePro');
    expect(meta('name', 'twitter:title')).toBe('Pricing — LumicorePro');
  });

  it('marks auth-style pages noindex,nofollow and defaults the canonical to the current URL', () => {
    render(<PageSEO title="Login" description="Sign in" noIndex />);

    expect(meta('name', 'robots')).toBe('noindex,nofollow');
    expect(
      document.querySelector('link[rel="canonical"]').getAttribute('href')
    ).toBe(window.location.href);
  });

  it('honours an explicit canonical URL', () => {
    render(
      <PageSEO
        title="Templates"
        description="Browse templates"
        canonicalUrl="https://lumicorepro.com/templates"
      />
    );

    expect(
      document.querySelector('link[rel="canonical"]').getAttribute('href')
    ).toBe('https://lumicorepro.com/templates');
    expect(meta('property', 'og:url')).toBe('https://lumicorepro.com/templates');
  });

  it('emits hreflang alternates for every supported locale plus x-default', () => {
    render(<PageSEO title="Home" description="Landing page" />);

    const links = alternateLinks();
    expect(links).toHaveLength(14);

    const byLang = Object.fromEntries(
      links.map((link) => [link.getAttribute('hreflang'), link.getAttribute('href')])
    );
    const origin = window.location.origin;
    const path = window.location.pathname === '/' ? '' : window.location.pathname;
    expect(byLang.en).toBe(`${origin}${path || '/'}`);
    expect(byLang.ar).toBe(`${origin}/ar${path}`);
    expect(byLang['x-default']).toBe(window.location.href);
  });

  it('injects JSON-LD schema scripts and replaces stale ones on rerender', () => {
    const organization = {
      '@context': 'https://schema.org',
      '@type': 'Organization',
      name: 'LumicorePro',
    };
    const website = {
      '@context': 'https://schema.org',
      '@type': 'WebSite',
      name: 'LumicorePro',
    };
    const webPage = {
      '@context': 'https://schema.org',
      '@type': 'WebPage',
      name: 'Docs',
    };

    const { rerender } = render(
      <PageSEO title="Home" description="Landing" schema={[organization, website]} />
    );

    let scripts = [...document.querySelectorAll('script[data-lumicore-schema]')];
    expect(scripts).toHaveLength(2);
    expect(scripts.map((script) => JSON.parse(script.textContent)['@type'])).toEqual([
      'Organization',
      'WebSite',
    ]);

    rerender(<PageSEO title="Docs" description="Documentation" schema={webPage} />);

    scripts = [...document.querySelectorAll('script[data-lumicore-schema]')];
    expect(scripts).toHaveLength(1);
    expect(JSON.parse(scripts[0].textContent)['@type']).toBe('WebPage');
  });
});
