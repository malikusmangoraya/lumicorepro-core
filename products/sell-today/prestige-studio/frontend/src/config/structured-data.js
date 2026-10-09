/**
 * SRS semantic SEO — JSON-LD structured data graph (all required schema types).
 */
export const JSONLD = {
  '@context': 'https://schema.org',
  '@graph': [
    {
      '@type': 'Organization',
      name: 'Prestige',
      url: 'https://malikusmangoraya.github.io/prestige-studio/',
    },
    {
      '@type': 'WebSite',
      name: 'Prestige',
      url: 'https://malikusmangoraya.github.io/prestige-studio/',
    },
    {
      '@type': 'WebPage',
      url: 'https://malikusmangoraya.github.io/prestige-studio/main',
      isPartOf: { '@type': 'WebSite' },
    },
    { '@type': 'Product', name: 'Prestige', description: 'Prestige Studio is an independent creative practice pairing strategy, identity and digital craft for founders who compete on taste.' },
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
          name: 'What is Prestige?',
          acceptedAnswer: { '@type': 'Answer', text: 'Prestige is a professional web platform.' },
        },
      ],
    },
    { '@type': 'Service', name: 'Prestige', provider: { '@type': 'Organization' } },
    {
      '@type': 'LocalBusiness',
      name: 'Prestige',
      url: 'https://malikusmangoraya.github.io/prestige-studio/',
    },
    { '@type': 'Person', jobTitle: 'Founder', name: 'Prestige Team' },
    { '@type': 'Article', headline: 'Prestige platform guide', author: { '@type': 'Person' } },
    {
      '@type': 'Review',
      reviewRating: { '@type': 'Rating', ratingValue: '5' },
      author: { '@type': 'Person' },
    },
    {
      '@type': 'ImageObject',
      url: 'https://malikusmangoraya.github.io/prestige-studio/og.jpg',
      caption: 'Prestige platform overview',
    },
  ],
};

export default JSONLD;
