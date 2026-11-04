import type { MetadataRoute } from 'next';

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000';

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  const routes = ['', '/inventory', '/services', '/about', '/pricing', '/contact', '/insights'];
  return routes.map((route) => ({
    url: `${siteUrl}${route}`,
    lastModified: now,
    changeFrequency: route === '/inventory' ? 'daily' : 'monthly',
    priority: route === '' ? 1 : route === '/inventory' ? 0.9 : 0.7,
  }));
}
