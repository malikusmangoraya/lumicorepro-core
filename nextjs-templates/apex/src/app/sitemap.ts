import type { MetadataRoute } from 'next';
import { prisma } from '@/lib/prisma';

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000';

export const dynamic = 'force-dynamic';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date();
  const staticRoutes = ['', '/inventory', '/shop', '/services', '/about', '/pricing', '/contact', '/insights'];

  const entries: MetadataRoute.Sitemap = staticRoutes.map((route) => ({
    url: `${siteUrl}${route}`,
    lastModified: now,
    changeFrequency: route === '/inventory' ? 'daily' : 'monthly',
    priority: route === '' ? 1 : route === '/inventory' ? 0.9 : 0.7,
  }));

  // The catalogue is the reason people come back, so it belongs in the map.
  try {
    const [vehicles, products] = await Promise.all([
      prisma.vehicle.findMany({
        where: { status: 'active' },
        select: { slug: true, updatedAt: true },
        take: 500,
      }),
      prisma.product.findMany({
        where: { isActive: true },
        select: { slug: true, updatedAt: true },
        take: 200,
      }),
    ]);

    for (const vehicle of vehicles) {
      entries.push({
        url: `${siteUrl}/inventory/${vehicle.slug}`,
        lastModified: vehicle.updatedAt,
        changeFrequency: 'weekly',
        priority: 0.8,
      });
    }

    // Shop products live on /shop until a product detail route exists.
    if (products.length > 0) {
      entries.push({
        url: `${siteUrl}/shop`,
        lastModified: products.reduce(
          (latest, product) => (product.updatedAt > latest ? product.updatedAt : latest),
          products[0].updatedAt,
        ),
        changeFrequency: 'weekly',
        priority: 0.8,
      });
    }
  } catch {
    // A database hiccup must not break the sitemap; the static routes still ship.
  }

  return entries;
}
