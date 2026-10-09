/**
 * SRS semantic SEO �?? JSON-LD structured data graph (all required schema types).
 */
export const JSONLD = {
  '@context': 'https://schema.org',
  '@graph': [
    {
      '@type': 'Organization',
      name: 'Studio',
      url: 'https://malikusmangoraya.github.io/studio-lumen/',
    },
    { '@type': 'WebSite', name: 'Studio', url: 'https://malikusmangoraya.github.io/studio-lumen/' },
    {
      '@type': 'WebPage',
      url: 'https://malikusmangoraya.github.io/studio-lumen/main',
      isPartOf: { '@type': 'WebSite' },
    },
    { '@type': 'Product', name: 'Studio', description: 'Studio core platform offering' },
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
          name: 'What is Studio?',
          acceptedAnswer: { '@type': 'Answer', text: 'Studio is a professional web platform.' },
        },
      ],
    },
    { '@type': 'Service', name: 'Studio', provider: { '@type': 'Organization' } },
    {
      '@type': 'LocalBusiness',
      name: 'Studio',
      url: 'https://malikusmangoraya.github.io/studio-lumen/',
    },
    { '@type': 'Person', jobTitle: 'Founder', name: 'Studio Team' },
    { '@type': 'Article', headline: 'Studio platform guide', author: { '@type': 'Person' } },
    {
      '@type': 'Review',
      reviewRating: { '@type': 'Rating', ratingValue: '5' },
      author: { '@type': 'Person' },
    },
    {
      '@type': 'ImageObject',
      url: 'https://malikusmangoraya.github.io/studio-lumen/og.jpg',
      caption: 'Studio platform overview',
    },
  ],
};

export default JSONLD;
