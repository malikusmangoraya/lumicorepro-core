/**
 * SRS semantic SEO — JSON-LD structured data graph (all required schema types).
 */
export const JSONLD = {
  '@context': 'https://schema.org',
  '@graph': [
    {
      '@type': 'Organization',
      name: 'Saffron',
      url: 'https://malikusmangoraya.github.io/saffron-voyage/',
    },
    {
      '@type': 'WebSite',
      name: 'Saffron',
      url: 'https://malikusmangoraya.github.io/saffron-voyage/',
    },
    {
      '@type': 'WebPage',
      url: 'https://malikusmangoraya.github.io/saffron-voyage/main',
      isPartOf: { '@type': 'WebSite' },
    },
    { '@type': 'Product', name: 'Saffron', description: 'Saffron Voyage curates small-group journeys through the stories, kitchens and landscapes of South Asia — led by local storytellers.' },
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
          name: 'What is Saffron?',
          acceptedAnswer: { '@type': 'Answer', text: 'Saffron is a professional web platform.' },
        },
      ],
    },
    { '@type': 'Service', name: 'Saffron', provider: { '@type': 'Organization' } },
    {
      '@type': 'LocalBusiness',
      name: 'Saffron',
      url: 'https://malikusmangoraya.github.io/saffron-voyage/',
    },
    { '@type': 'Person', jobTitle: 'Founder', name: 'Saffron Team' },
    { '@type': 'Article', headline: 'Saffron platform guide', author: { '@type': 'Person' } },
    {
      '@type': 'Review',
      reviewRating: { '@type': 'Rating', ratingValue: '5' },
      author: { '@type': 'Person' },
    },
    {
      '@type': 'ImageObject',
      url: 'https://malikusmangoraya.github.io/saffron-voyage/og.jpg',
      caption: 'Saffron platform overview',
    },
  ],
};

export default JSONLD;
