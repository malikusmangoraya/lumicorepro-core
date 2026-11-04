import type { MetadataRoute } from 'next';
import { site } from '@/lib/site-config';

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: site.name,
    short_name: 'Apex',
    description:
      'A curated inventory of performance and collector cars, with provenance verification and private viewings.',
    start_url: '/',
    display: 'standalone',
    background_color: '#070913',
    theme_color: '#070913',
    orientation: 'portrait-primary',
    icons: [
      { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
      { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
      { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
    ],
  };
}
