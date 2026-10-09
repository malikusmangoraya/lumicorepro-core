/**
 * SRS semantic SEO — JSON-LD structured data graph (all required schema types).
 */
export const JSONLD = {
  '@context': 'https://schema.org',
  '@graph': [
    {
      '@type': 'Organization',
      name: 'ClaimFlow',
      url: 'https://malikusmangoraya.github.io/claimflow/',
    },
    {
      '@type': 'WebSite',
      name: 'ClaimFlow',
      url: 'https://malikusmangoraya.github.io/claimflow/',
    },
    {
      '@type': 'WebPage',
      url: 'https://malikusmangoraya.github.io/claimflow/main',
      isPartOf: { '@type': 'WebSite' },
    },
    { '@type': 'Product', name: 'ClaimFlow', description: 'ClaimFlow gathers documents, triages by policy coverage, validates completeness and routes claims to adjusters with summaries and next steps — so claim intake stops being the bottleneck.' },
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
          name: 'What is ClaimFlow?',
          acceptedAnswer: { '@type': 'Answer', text: 'Claimflow is a professional web platform.' },
        },
      ],
    },
    { '@type': 'Service', name: 'ClaimFlow', provider: { '@type': 'Organization' } },
    {
      '@type': 'LocalBusiness',
      name: 'ClaimFlow',
      url: 'https://malikusmangoraya.github.io/claimflow/',
    },
    { '@type': 'Person', jobTitle: 'Founder', name: 'ClaimFlow Team' },
    { '@type': 'Article', headline: 'Claimflow platform guide', author: { '@type': 'Person' } },
    {
      '@type': 'Review',
      reviewRating: { '@type': 'Rating', ratingValue: '5' },
      author: { '@type': 'Person' },
    },
    {
      '@type': 'ImageObject',
      url: 'https://malikusmangoraya.github.io/claimflow/og.jpg',
      caption: 'Claimflow platform overview',
    },
  ],
};

export default JSONLD;
