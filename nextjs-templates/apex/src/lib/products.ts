import { prisma } from '@/lib/prisma';
import { parseJson } from '@/lib/utils';

export type ShopProduct = {
  id: string;
  slug: string;
  title: string;
  description: string;
  price: number;
  comparePrice: number | null;
  currency: string;
  stock: number;
  image: string | null;
  rating: number;
  category: string | null;
};

export async function getProductBySlug(slug: string): Promise<ShopProduct | null> {
  try {
    const row = await prisma.product.findFirst({
      where: { slug, isActive: true },
      include: { category: { select: { name: true } } },
    });
    if (!row) return null;
    const images = parseJson<string[]>(row.images, []);
    return {
      id: row.id,
      slug: row.slug,
      title: row.title,
      description: row.description,
      price: row.price,
      comparePrice: row.comparePrice,
      currency: 'USD',
      stock: row.stock,
      image: row.thumbnail ?? images[0] ?? null,
      rating: row.rating,
      category: row.category?.name ?? null,
    };
  } catch {
    return null;
  }
}

export async function listProducts(): Promise<{ items: ShopProduct[]; ready: boolean }> {
  try {
    const rows = await prisma.product.findMany({
      where: { isActive: true },
      orderBy: [{ isFeatured: 'desc' }, { title: 'asc' }],
      include: { category: { select: { name: true } } },
    });

    return {
      ready: true,
      items: rows.map((row) => {
        const images = parseJson<string[]>(row.images, []);
        return {
          id: row.id,
          slug: row.slug,
          title: row.title,
          description: row.description,
          price: row.price,
          comparePrice: row.comparePrice,
          currency: 'USD',
          stock: row.stock,
          image: row.thumbnail ?? images[0] ?? null,
          rating: row.rating,
          category: row.category?.name ?? null,
        };
      }),
    };
  } catch {
    return { items: [], ready: false };
  }
}
