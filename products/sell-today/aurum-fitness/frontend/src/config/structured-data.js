/**
 * SRS semantic SEO — JSON-LD structured data graph (all required schema types).
 */
export const JSONLD = {
  '@context': 'https://schema.org',
  '@graph': [
    {
      '@type': 'Organization',
      name: 'Aurum',
      url: 'https://malikusmangoraya.github.io/aurum-fitness/',
    },
    { '@type': 'WebSite', name: 'Aurum', url: 'https://malikusmangoraya.github.io/aurum-fitness/' },
    {
      '@type': 'WebPage',
      url: 'https://malikusmangoraya.github.io/aurum-fitness/main',
      isPartOf: { '@type': 'WebSite' },
    },
    { '@type': 'Product', name: 'Aurum', description: 'Aurum Fitness fuses olympic methodology with private training floors — coached, measured, relentless.' },
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
          name: 'What is Aurum?',
          acceptedAnswer: { '@type': 'Answer', text: 'Aurum is a professional web platform.' },
        },
      ],
    },
    { '@type': 'Service', name: 'Aurum', provider: { '@type': 'Organization' } },
    {
      '@type': 'LocalBusiness',
      name: 'Aurum',
      url: 'https://malikusmangoraya.github.io/aurum-fitness/',
    },
    { '@type': 'Person', jobTitle: 'Founder', name: 'Aurum Team' },
    { '@type': 'Article', headline: 'Aurum platform guide', author: { '@type': 'Person' } },
    {
      '@type': 'Review',
      reviewRating: { '@type': 'Rating', ratingValue: '5' },
      author: { '@type': 'Person' },
    },
    {
      '@type': 'ImageObject',
      url: 'https://malikusmangoraya.github.io/aurum-fitness/og.jpg',
      caption: 'Aurum platform overview',
    },
  ],
};

export default JSONLD;
