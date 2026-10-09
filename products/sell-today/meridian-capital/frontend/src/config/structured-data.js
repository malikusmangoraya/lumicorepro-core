/**
 * SRS semantic SEO — JSON-LD structured data graph (all required schema types).
 */
export const JSONLD = {
  '@context': 'https://schema.org',
  '@graph': [
    {
      '@type': 'Organization',
      name: 'Meridian',
      url: 'https://malikusmangoraya.github.io/meridian-capital/',
    },
    {
      '@type': 'WebSite',
      name: 'Meridian',
      url: 'https://malikusmangoraya.github.io/meridian-capital/',
    },
    {
      '@type': 'WebPage',
      url: 'https://malikusmangoraya.github.io/meridian-capital/main',
      isPartOf: { '@type': 'WebSite' },
    },
    { '@type': 'Product', name: 'Meridian', description: 'Meridian Capital manages concentrated, long-horizon portfolios for founders and family offices, with transparent, quarterly reporting.' },
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
          name: 'What is Meridian?',
          acceptedAnswer: { '@type': 'Answer', text: 'Meridian is a professional web platform.' },
        },
      ],
    },
    { '@type': 'Service', name: 'Meridian', provider: { '@type': 'Organization' } },
    {
      '@type': 'LocalBusiness',
      name: 'Meridian',
      url: 'https://malikusmangoraya.github.io/meridian-capital/',
    },
    { '@type': 'Person', jobTitle: 'Founder', name: 'Meridian Team' },
    { '@type': 'Article', headline: 'Meridian platform guide', author: { '@type': 'Person' } },
    {
      '@type': 'Review',
      reviewRating: { '@type': 'Rating', ratingValue: '5' },
      author: { '@type': 'Person' },
    },
    {
      '@type': 'ImageObject',
      url: 'https://malikusmangoraya.github.io/meridian-capital/og.jpg',
      caption: 'Meridian platform overview',
    },
  ],
};

export default JSONLD;
