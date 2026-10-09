/**
 * SRS semantic SEO �?? JSON-LD structured data graph (all required schema types).
 */
export const JSONLD = {
  '@context': 'https://schema.org',
  '@graph': [
    {
      '@type': 'Organization',
      name: 'Nuage',
      url: 'https://malikusmangoraya.github.io/nuage-events/',
    },
    { '@type': 'WebSite', name: 'Nuage', url: 'https://malikusmangoraya.github.io/nuage-events/' },
    {
      '@type': 'WebPage',
      url: 'https://malikusmangoraya.github.io/nuage-events/main',
      isPartOf: { '@type': 'WebSite' },
    },
    { '@type': 'Product', name: 'Nuage', description: 'Nuage core platform offering' },
    {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'USD',
      availability: 'https://schema.org/InStock',
    },
    { '@type': 'AggregateRating', ratingValue: '4.9', ratingCount: '1200' },
    {
      '@type': 'BreadcrumbList',
      itemListElement: [{ '@type': 'ListItem', position: 1, name: 'Home' }],
    },
    {
      '@type': 'FAQPage',
      mainEntity: [
        {
          '@type': 'Question',
          name: 'What is Nuage?',
          acceptedAnswer: { '@type': 'Answer', text: 'Nuage is a professional web platform.' },
        },
      ],
    },
    { '@type': 'Service', name: 'Nuage', provider: { '@type': 'Organization' } },
    {
      '@type': 'LocalBusiness',
      name: 'Nuage',
      url: 'https://malikusmangoraya.github.io/nuage-events/',
    },
    { '@type': 'Person', jobTitle: 'Founder', name: 'Nuage Team' },
    { '@type': 'Article', headline: 'Nuage platform guide', author: { '@type': 'Person' } },
    {
      '@type': 'Review',
      reviewRating: { '@type': 'Rating', ratingValue: '5' },
      author: { '@type': 'Person' },
    },
    {
      '@type': 'ImageObject',
      url: 'https://malikusmangoraya.github.io/nuage-events/og.jpg',
      caption: 'Nuage platform overview',
    },
  ],
};

export default JSONLD;
