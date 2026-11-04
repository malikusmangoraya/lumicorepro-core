import Image from 'next/image';
import Link from 'next/link';
import { Star } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { AddToCartButton } from '@/components/shop/add-to-cart-button';
import { formatCurrency } from '@/lib/utils';
import type { ShopProduct } from '@/lib/products';

export function ProductCard({ product }: { product: ShopProduct }) {
  const outOfStock = product.stock <= 0;

  return (
    <article className="flex flex-col overflow-hidden rounded-panel border border-line bg-surface/70 transition-colors hover:border-primary/50">
      <div className="relative aspect-square overflow-hidden bg-canvas">
        {product.image ? (
          <Image
            src={product.image}
            alt={product.title}
            fill
            sizes="(max-width: 768px) 50vw, 33vw"
            className="object-cover transition-transform duration-500 hover:scale-[1.03]"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-muted">No image</div>
        )}
        {product.category && (
          <div className="absolute left-3 top-3">
            <Badge tone="neutral" className="border-white/20 bg-canvas/85 text-heading backdrop-blur">
              {product.category}
            </Badge>
          </div>
        )}
        {outOfStock && (
          <div className="absolute inset-0 flex items-center justify-center bg-canvas/70">
            <Badge tone="danger">Out of stock</Badge>
          </div>
        )}
      </div>

      <div className="flex flex-1 flex-col p-5">
        <h3 className="font-display text-base font-600 text-heading">
          <Link href={`/shop/${product.slug}`} className="hover:text-accent">
            {product.title}
          </Link>
        </h3>
        <p className="mt-1 flex-1 text-sm leading-relaxed text-muted">{product.description}</p>

        <div className="mt-3 flex items-center justify-between gap-3">
          <p className="font-display text-lg font-700 text-accent">
            {formatCurrency(product.price, product.currency)}
          </p>
          <p className="flex items-center gap-1 text-xs text-muted">
            <Star className="size-3 fill-current text-amber-300" aria-hidden="true" />
            {product.rating.toFixed(1)}
            <span className="text-muted/70">({product.stock} in stock)</span>
          </p>
        </div>

        <div className="mt-4">
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
      </div>
    </article>
  );
}
