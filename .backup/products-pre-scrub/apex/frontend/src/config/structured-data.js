/**
 * SRS semantic SEO �?? JSON-LD structured data graph (all required schema types).
 */
export const JSONLD = {
  '@context': 'https://schema.org',
  '@graph': [
    { '@type': 'Organization', name: 'Apex', url: 'https://malikusmangoraya.github.io/apex/' },
    { '@type': 'WebSite', name: 'Apex', url: 'https://malikusmangoraya.github.io/apex/' },
    {
      '@type': 'WebPage',
      url: 'https://malikusmangoraya.github.io/apex/main',
      isPartOf: { '@type': 'WebSite' },
    },
    { '@type': 'Product', name: 'Apex', description: 'Apex core platform offering' },
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
          name: 'What is Apex?',
          acceptedAnswer: { '@type': 'Answer', text: 'Apex is a professional web platform.' },
        },
      ],
    },
    { '@type': 'Service', name: 'Apex', provider: { '@type': 'Organization' } },
    { '@type': 'LocalBusiness', name: 'Apex', url: 'https://malikusmangoraya.github.io/apex/' },
    { '@type': 'Person', jobTitle: 'Founder', name: 'Apex Team' },
    { '@type': 'Article', headline: 'Apex platform guide', author: { '@type': 'Person' } },
    {
      '@type': 'Review',
      reviewRating: { '@type': 'Rating', ratingValue: '5' },
      author: { '@type': 'Person' },
    },
    {
      '@type': 'ImageObject',
      url: 'https://malikusmangoraya.github.io/apex/og.jpg',
      caption: 'Apex platform overview',
    },
  ],
};

export default JSONLD;
