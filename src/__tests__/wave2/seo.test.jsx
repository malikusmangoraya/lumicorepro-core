import { describe, it, expect, beforeEach } from 'vitest';
import { render } from '@testing-library/react';
import SEO, {
  schemas,
  hreflangFor,
  seoLocales,
  resolveThemeColor,
} from '../../components/common/SEO';

const HEAD_SELECTOR =
  'meta, link[rel="canonical"], link[rel="alternate"][hreflang], script[data-lumicore-schema]';

const metaContent = (attr, value) =>
  document.querySelector(`meta[${attr}="${value}"]`)?.getAttribute('content');

beforeEach(() => {
  document.head.querySelectorAll(HEAD_SELECTOR).forEach((node) => node.remove());
  document.title = '';
  document.documentElement.style.removeProperty('--t-primary');
});

describe('schemas.organization', () => {
  it('builds an Organization with an ImageObject logo and default sameAs', () => {
    const org = schemas.organization({
      name: 'Acme',
      url: 'https://acme.test',
      logo: 'https://acme.test/logo.png',
      description: 'Tools for teams',
    });

    expect(org['@context']).toBe('https://schema.org');
    expect(org['@type']).toBe('Organization');
    expect(org.logo).toEqual({ '@type': 'ImageObject', url: 'https://acme.test/logo.png' });
    expect(org.sameAs).toEqual([]);
  });

  it('omits the logo when none is supplied', () => {
    const org = schemas.organization({ name: 'Acme', url: 'https://acme.test' });
    expect(org.logo).toBeUndefined();
  });
});

describe('schemas.product', () => {
  it('wraps price, currency and availability in a schema.org Offer', () => {
    const product = schemas.product({
      name: 'Headphones',
      price: '199.00',
      sku: 'HP-1',
      brand: 'Acme',
      rating: 4.6,
      reviewCount: 87,
    });

    expect(product['@type']).toBe('Product');
    expect(product.brand).toEqual({ '@type': 'Brand', name: 'Acme' });
    expect(product.offers).toMatchObject({
      '@type': 'Offer',
      price: '199.00',
      priceCurrency: 'USD',
      availability: 'https://schema.org/InStock',
      url: window.location.href,
    });
    expect(product.aggregateRating).toEqual({
      '@type': 'AggregateRating',
      ratingValue: 4.6,
      reviewCount: 87,
    });
  });

  it('supports overrides and omits aggregateRating without a rating', () => {
    const product = schemas.product({
      name: 'Cable',
      price: '9.00',
      currency: 'EUR',
      availability: 'OutOfStock',
    });

    expect(product.offers.priceCurrency).toBe('EUR');
    expect(product.offers.availability).toBe('https://schema.org/OutOfStock');
    expect('aggregateRating' in product).toBe(false);
  });
});

describe('schemas.faq and schemas.breadcrumb', () => {
  it('maps FAQ items to Question/Answer entities', () => {
    const faq = schemas.faq([
      { question: 'Does it scale?', answer: 'Yes.' },
      { question: 'Is there a trial?', answer: '14 days.' },
    ]);

    expect(faq['@type']).toBe('FAQPage');
    expect(faq.mainEntity).toHaveLength(2);
    expect(faq.mainEntity[0]).toEqual({
      '@type': 'Question',
      name: 'Does it scale?',
      acceptedAnswer: { '@type': 'Answer', text: 'Yes.' },
    });
  });

  it('numbers breadcrumb items from 1', () => {
    const crumb = schemas.breadcrumb([
      { name: 'Home', url: 'https://acme.test/' },
      { name: 'Pricing', url: 'https://acme.test/pricing' },
    ]);

    expect(crumb.itemListElement.map((item) => item.position)).toEqual([1, 2]);
    expect(crumb.itemListElement[1]).toMatchObject({
      name: 'Pricing',
      item: 'https://acme.test/pricing',
    });
  });
});

describe('schemas.article, event, softwareApp, localBusiness', () => {
  it('falls back to the publish date when dateModified is absent', () => {
    const article = schemas.article({
      headline: 'Launch',
      datePublished: '2026-10-01',
      authorName: 'Ada',
      publisherName: 'Acme',
    });

    expect(article.dateModified).toBe('2026-10-01');
    expect(article.author).toEqual({ '@type': 'Person', name: 'Ada' });
    expect(article.publisher.name).toBe('Acme');
  });

  it('uses VirtualLocation for online events and Place for physical ones', () => {
    const online = schemas.event({
      name: 'Webinar',
      startDate: '2026-11-01',
      url: 'https://acme.test/live',
      isOnline: true,
    });
    expect(online.location).toEqual({
      '@type': 'VirtualLocation',
      url: 'https://acme.test/live',
    });
    expect(online.eventAttendanceMode).toBe('https://schema.org/OnlineEventAttendanceMode');

    const offline = schemas.event({
      name: 'Meetup',
      startDate: '2026-11-02',
      location: { name: 'Hub', streetAddress: '1 Main St', addressLocality: 'Lahore' },
    });
    expect(offline.location['@type']).toBe('Place');
    expect(offline.location.address.streetAddress).toBe('1 Main St');
  });

  it('applies software application defaults', () => {
    const app = schemas.softwareApp({ name: 'LumiCore', description: 'Studio' });

    expect(app['@type']).toBe('SoftwareApplication');
    expect(app.applicationCategory).toBe('BusinessApplication');
    expect(app.operatingSystem).toBe('All');
    expect(app.offers).toEqual({ '@type': 'Offer', price: '0.00', priceCurrency: 'USD' });
  });

  it('maps local business addresses, geo and opening hours', () => {
    const shop = schemas.localBusiness({
      name: 'Cafe',
      address: { streetAddress: '5 High St', addressLocality: 'Leeds' },
      geo: { lat: 53.8, lng: -1.55 },
      openingHours: ['Mo-Fr 09:00-17:00'],
    });

    expect(shop.address['@type']).toBe('PostalAddress');
    expect(shop.address.streetAddress).toBe('5 High St');
    expect(shop.geo).toEqual({ '@type': 'GeoCoordinates', latitude: 53.8, longitude: -1.55 });
    expect(shop.openingHours).toEqual(['Mo-Fr 09:00-17:00']);

    const empty = schemas.localBusiness({ name: 'Kiosk', address: {} });
    expect('openingHours' in empty).toBe(false);
    expect(schemas.restaurant({ name: 'Bistro' })['@type']).toBe('Restaurant');
  });

  it('builds a review with aggregate rating', () => {
    const review = schemas.review({ itemName: 'Headphones', ratingValue: 4.5, reviewCount: 40 });
    expect(review.itemReviewed).toEqual({ '@type': 'Thing', name: 'Headphones' });
    expect(review.reviewRating.bestRating).toBe(5);
    expect(review.aggregateRating.reviewCount).toBe(40);
  });
});

describe('hreflangFor', () => {
  it('returns every supported locale with prefixed paths', () => {
    const map = hreflangFor('/pricing', 'https://lumicorepro.com');

    expect(Object.keys(map)).toHaveLength(Object.keys(seoLocales).length);
    expect(map.en).toBe('https://lumicorepro.com/pricing');
    expect(map.fr).toBe('https://lumicorepro.com/fr/pricing');
    expect(map.ar).toBe('https://lumicorepro.com/ar/pricing');
  });

  it('keeps English at the bare root and prefixes the rest', () => {
    const map = hreflangFor('/', 'https://lumicorepro.com');

    expect(map.en).toBe('https://lumicorepro.com/');
    expect(map.es).toBe('https://lumicorepro.com/es');
  });

  it('supports a relative origin', () => {
    const map = hreflangFor('/blog', '');
    expect(map.en).toBe('/blog');
    expect(map.ur).toBe('/ur/blog');
  });
});

describe('SEO component', () => {
  it('writes title, description, canonical, robots and social metadata', () => {
    render(
      <SEO
        title="Pricing — LumiCorePro"
        description="Simple plans for every team."
        canonicalUrl="https://lumicorepro.com/pricing"
      />
    );

    expect(document.title).toBe('Pricing — LumiCorePro');
    expect(metaContent('name', 'description')).toBe('Simple plans for every team.');
    expect(metaContent('name', 'robots')).toBe('index,follow');
    expect(metaContent('property', 'og:title')).toBe('Pricing — LumiCorePro');
    expect(metaContent('property', 'og:url')).toBe('https://lumicorepro.com/pricing');
    expect(metaContent('name', 'twitter:card')).toBe('summary_large_image');
    expect(document.querySelector('link[rel="canonical"]').getAttribute('href')).toBe(
      'https://lumicorepro.com/pricing'
    );
  });

  it('marks noIndex pages as noindex,nofollow', () => {
    render(<SEO title="Draft" noIndex />);
    expect(metaContent('name', 'robots')).toBe('noindex,nofollow');
  });

  it('writes and replaces JSON-LD blocks without duplicating them', () => {
    const schema = [
      schemas.organization({ name: 'Acme', url: 'https://acme.test' }),
      schemas.website({ name: 'Acme', url: 'https://acme.test' }),
    ];
    const { rerender } = render(<SEO title="Acme" schema={schema} />);

    let scripts = [...document.querySelectorAll('script[data-lumicore-schema]')];
    expect(scripts).toHaveLength(2);
    expect(scripts.map((s) => JSON.parse(s.textContent)['@type'])).toEqual([
      'Organization',
      'WebSite',
    ]);

    rerender(
      <SEO
        title="Acme"
        schema={schemas.faq([{ question: 'Q', answer: 'A' }])}
      />
    );

    scripts = [...document.querySelectorAll('script[data-lumicore-schema]')];
    expect(scripts).toHaveLength(1);
    expect(JSON.parse(scripts[0].textContent)['@type']).toBe('FAQPage');
  });

  it('falls back to a SoftwareApplication schema when none is given', () => {
    render(<SEO title="Home" canonicalUrl="https://lumicorepro.com/" />);

    const scripts = [...document.querySelectorAll('script[data-lumicore-schema]')];
    expect(scripts).toHaveLength(1);
    const jsonLd = JSON.parse(scripts[0].textContent);
    expect(jsonLd['@type']).toBe('SoftwareApplication');
    expect(jsonLd.name).toBe('LumiCorePro');
    expect(jsonLd.url).toBe('https://lumicorepro.com/');
  });

  it('emits hreflang alternates plus x-default', () => {
    render(
      <SEO
        title="Pricing"
        canonicalUrl="https://lumicorepro.com/pricing"
        hreflang={hreflangFor('/pricing', 'https://lumicorepro.com')}
        locale="fr_FR"
      />
    );

    const links = [...document.querySelectorAll('link[rel="alternate"][hreflang]')];
    expect(links).toHaveLength(Object.keys(seoLocales).length + 1);
    expect(links.find((l) => l.getAttribute('hreflang') === 'ar').getAttribute('href')).toBe(
      'https://lumicorepro.com/ar/pricing'
    );
    expect(links.find((l) => l.getAttribute('hreflang') === 'x-default').getAttribute('href')).toBe(
      'https://lumicorepro.com/pricing'
    );
    expect(metaContent('property', 'og:locale')).toBe('fr_FR');
  });

  it('never lists the active locale among og:locale alternates', () => {
    render(<SEO title="Pricing" locale="en_US" />);

    const alternates = [...document.querySelectorAll('meta[property="og:locale:alternate"]')].map(
      (el) => el.getAttribute('content')
    );
    expect(alternates.length).toBeGreaterThan(0);
    expect(alternates).not.toContain('en_US');
  });

  it('resolves a concrete theme-color instead of a var() reference', () => {
    render(<SEO title="Theme" />);
    expect(resolveThemeColor()).toBe('#0D9488');
    expect(metaContent('name', 'theme-color')).toBe('#0D9488');
  });
});
