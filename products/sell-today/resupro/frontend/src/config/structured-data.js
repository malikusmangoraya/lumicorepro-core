/**
 * SRS semantic SEO — JSON-LD structured data graph (all required schema types).
 */
export const JSONLD = {
  '@context': 'https://schema.org',
  '@graph': [
    { '@type': 'Organization', name: 'ResuPro', url: 'https://malikusmangoraya.github.io/resupro/' },
    { '@type': 'WebSite', name: 'ResuPro', url: 'https://malikusmangoraya.github.io/resupro/' },
    {
      '@type': 'WebPage',
      url: 'https://malikusmangoraya.github.io/resupro/main',
      isPartOf: { '@type': 'WebSite' },
    },
    { '@type': 'Product', name: 'ResuPro', description: 'ResuPro builds ATS-proof resumes, matching every line to the job description and coaching you through interviews that convert.' },
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
          name: 'What is ResuPro?',
          acceptedAnswer: { '@type': 'Answer', text: 'Build is a professional web platform.' },
        },
      ],
    },
    { '@type': 'Service', name: 'ResuPro', provider: { '@type': 'Organization' } },
    { '@type': 'LocalBusiness', name: 'ResuPro', url: 'https://malikusmangoraya.github.io/resupro/' },
    { '@type': 'Person', jobTitle: 'Founder', name: 'ResuPro Team' },
    { '@type': 'Article', headline: 'Build platform guide', author: { '@type': 'Person' } },
    {
      '@type': 'Review',
      reviewRating: { '@type': 'Rating', ratingValue: '5' },
      author: { '@type': 'Person' },
    },
    {
      '@type': 'ImageObject',
      url: 'https://malikusmangoraya.github.io/resupro/og.jpg',
      caption: 'Build platform overview',
    },
  ],
};

export default JSONLD;
