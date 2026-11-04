import type { Metadata } from 'next';
import Image from 'next/image';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ArrowLeft, Check, Package } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Panel } from '@/components/ui/card';
import { Section } from '@/components/ui/section';
import { Stars } from '@/components/ui/stars';
import { AddToCartButton } from '@/components/shop/add-to-cart-button';
import { ReviewsSection } from '@/components/reviews/reviews-section';
import { getProductBySlug } from '@/lib/products';
import { formatCurrency } from '@/lib/utils';

export const dynamic = 'force-dynamic';

type Params = Promise<{ slug: string }>;

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000';

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { slug } = await params;
  const product = await getProductBySlug(slug);
  if (!product) return { title: 'Product not found' };
  return {
    title: product.title,
    description: product.description,
    alternates: { canonical: `/shop/${product.slug}` },
    openGraph: {
      title: product.title,
      description: product.description,
      images: product.image ? [{ url: product.image }] : undefined,
    },
  };
}

export default async function ProductPage({ params }: { params: Params }) {
  const { slug } = await params;
  const product = await getProductBySlug(slug);
  if (!product) notFound();

  const outOfStock = product.stock <= 0;

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: product.title,
    description: product.description,
    image: product.image ? [`${siteUrl}${product.image}`] : undefined,
    category: product.category ?? undefined,
    offers: {
      '@type': 'Offer',
      price: product.price,
      priceCurrency: product.currency,
      availability: outOfStock
        ? 'https://schema.org/OutOfStock'
        : 'https://schema.org/InStock',
      url: `${siteUrl}/shop/${product.slug}`,
    },
    ...(product.rating > 0
      ? { aggregateRating: { '@type': 'AggregateRating', ratingValue: product.rating, reviewCount: 1 } }
      : {}),
  };

  return (
    <>
      <Section>
        <Link
          href="/shop"
          className="inline-flex items-center gap-1.5 text-sm text-muted transition-colors hover:text-heading"
        >
          <ArrowLeft className="size-4" aria-hidden="true" />
          Back to the shop
        </Link>

        <div className="mt-6 grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="relative aspect-square overflow-hidden rounded-panel border border-line bg-canvas">
            {product.image ? (
              <Image
                src={product.image}
                alt={product.title}
                fill
                priority
                sizes="(max-width: 1024px) 100vw, 55vw"
                className="object-cover"
              />
            ) : (
              <div className="flex h-full items-center justify-center text-sm text-muted">
                No image
              </div>
            )}
          </div>

          <div>
            <div className="flex flex-wrap items-center gap-2">
              {product.category && <Badge tone="neutral">{product.category}</Badge>}
              {outOfStock ? (
                <Badge tone="danger">Out of stock</Badge>
              ) : (
                <Badge tone="success">{product.stock} in stock</Badge>
              )}
            </div>

            <h1 className="mt-4 text-balance font-display text-3xl font-700 leading-tight text-heading">
              {product.title}
            </h1>

            <div className="mt-2 flex items-center gap-2 text-sm text-muted">
              <Stars rating={product.rating} />
              {product.rating.toFixed(1)}
            </div>

            <p className="mt-5 text-pretty text-sm leading-relaxed text-body/85">
              {product.description}
            </p>

            <p className="mt-6 font-display text-3xl font-700 text-accent">
              {formatCurrency(product.price, product.currency)}
            </p>
            {product.comparePrice && product.comparePrice > product.price && (
              <p className="mt-1 text-sm text-muted line-through">
                {formatCurrency(product.comparePrice, product.currency)}
              </p>
            )}

            <div className="mt-6">
              <AddToCartButton
                kind="product"
                slug={product.slug}
                title={product.title}
                price={product.price}
                currency={product.currency}
                image={product.image}
                disabled={outOfStock}
              />
            </div>

            <ul className="mt-6 space-y-2 border-t border-line/60 pt-4 text-sm text-muted">
              <li className="flex items-center gap-2">
                <Package className="size-4 text-accent" aria-hidden="true" />
                Dispatched from the workshop within two working days
              </li>
              <li className="flex items-center gap-2">
                <Check className="size-4 text-accent" aria-hidden="true" />
                Returns accepted within 30 days, unused
              </li>
            </ul>
          </div>
        </div>

        <Panel className="mt-8 p-6">
          <ReviewsSection target={{ kind: 'product', id: product.id, slug: product.slug }} />
        </Panel>
      </Section>

      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
    </>
  );
}
