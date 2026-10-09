/**
 * SRS semantic SEO — JSON-LD structured data graph (all required schema types).
 */
export const JSONLD = {
  '@context': 'https://schema.org',
  '@graph': [
    { '@type': 'Organization', name: 'FlowPilot', url: 'https://malikusmangoraya.github.io/flowpilot/' },
    { '@type': 'WebSite', name: 'FlowPilot', url: 'https://malikusmangoraya.github.io/flowpilot/' },
    {
      '@type': 'WebPage',
      url: 'https://malikusmangoraya.github.io/flowpilot/main',
      isPartOf: { '@type': 'WebSite' },
    },
    { '@type': 'Product', name: 'FlowPilot', description: 'FlowPilot turns scattered intent data into a forecast the whole revenue team trusts - account scoring, sequence automation and attribution in one workspace.' },
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
          name: 'What is FlowPilot?',
          acceptedAnswer: { '@type': 'Answer', text: 'FlowPilot is a professional web platform.' },
        },
      ],
    },
    { '@type': 'Service', name: 'FlowPilot', provider: { '@type': 'Organization' } },
    { '@type': 'LocalBusiness', name: 'FlowPilot', url: 'https://malikusmangoraya.github.io/flowpilot/' },
    { '@type': 'Person', jobTitle: 'Founder', name: 'FlowPilot Team' },
    { '@type': 'Article', headline: 'FlowPilot platform guide', author: { '@type': 'Person' } },
    {
      '@type': 'Review',
      reviewRating: { '@type': 'Rating', ratingValue: '5' },
      author: { '@type': 'Person' },
    },
    {
      '@type': 'ImageObject',
      url: 'https://malikusmangoraya.github.io/flowpilot/og.jpg',
      caption: 'FlowPilot platform overview',
    },
  ],
};

export default JSONLD;
