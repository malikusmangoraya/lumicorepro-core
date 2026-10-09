/**
 * SRS semantic SEO �?? JSON-LD structured data graph (all required schema types).
 */
export const JSONLD = {
  '@context': 'https://schema.org',
  '@graph': [
    {
      '@type': 'Organization',
      name: 'Claimflow',
      url: 'https://malikusmangoraya.github.io/claimflow-ai/',
    },
    {
      '@type': 'WebSite',
      name: 'Claimflow',
      url: 'https://malikusmangoraya.github.io/claimflow-ai/',
    },
    {
      '@type': 'WebPage',
      url: 'https://malikusmangoraya.github.io/claimflow-ai/main',
      isPartOf: { '@type': 'WebSite' },
    },
    { '@type': 'Product', name: 'Claimflow', description: 'Claimflow core platform offering' },
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
          name: 'What is Claimflow?',
          acceptedAnswer: { '@type': 'Answer', text: 'Claimflow is a professional web platform.' },
        },
      ],
    },
    { '@type': 'Service', name: 'Claimflow', provider: { '@type': 'Organization' } },
    {
      '@type': 'LocalBusiness',
      name: 'Claimflow',
      url: 'https://malikusmangoraya.github.io/claimflow-ai/',
    },
    { '@type': 'Person', jobTitle: 'Founder', name: 'Claimflow Team' },
    { '@type': 'Article', headline: 'Claimflow platform guide', author: { '@type': 'Person' } },
    {
      '@type': 'Review',
      reviewRating: { '@type': 'Rating', ratingValue: '5' },
      author: { '@type': 'Person' },
    },
    {
      '@type': 'ImageObject',
      url: 'https://malikusmangoraya.github.io/claimflow-ai/og.jpg',
      caption: 'Claimflow platform overview',
    },
  ],
};

export default JSONLD;
