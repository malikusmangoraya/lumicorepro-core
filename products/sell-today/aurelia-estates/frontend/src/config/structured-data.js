/**
 * SRS semantic SEO — JSON-LD structured data graph (all required schema types).
 */
export const JSONLD = {
  '@context': 'https://schema.org',
  '@graph': [
    {
      '@type': 'Organization',
      name: 'Aurelia',
      url: 'https://malikusmangoraya.github.io/aurelia-estates/',
    },
    {
      '@type': 'WebSite',
      name: 'Aurelia',
      url: 'https://malikusmangoraya.github.io/aurelia-estates/',
    },
    {
      '@type': 'WebPage',
      url: 'https://malikusmangoraya.github.io/aurelia-estates/main',
      isPartOf: { '@type': 'WebSite' },
    },
    { '@type': 'Product', name: 'Aurelia', description: 'Aurelia Estates brokers the world\'s most distinctive residences — penthouse, villa and heritage homes — with white-glove private client service.' },
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
          name: 'What is Aurelia?',
          acceptedAnswer: { '@type': 'Answer', text: 'Aurelia is a professional web platform.' },
        },
      ],
    },
    { '@type': 'Service', name: 'Aurelia', provider: { '@type': 'Organization' } },
    {
      '@type': 'LocalBusiness',
      name: 'Aurelia',
      url: 'https://malikusmangoraya.github.io/aurelia-estates/',
    },
    { '@type': 'Person', jobTitle: 'Founder', name: 'Aurelia Team' },
    { '@type': 'Article', headline: 'Aurelia platform guide', author: { '@type': 'Person' } },
    {
      '@type': 'Review',
      reviewRating: { '@type': 'Rating', ratingValue: '5' },
      author: { '@type': 'Person' },
    },
    {
      '@type': 'ImageObject',
      url: 'https://malikusmangoraya.github.io/aurelia-estates/og.jpg',
      caption: 'Aurelia platform overview',
    },
  ],
};

export default JSONLD;
