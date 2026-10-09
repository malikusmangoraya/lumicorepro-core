import React, { useState } from 'react';
import { ShoppingCart, Heart } from 'lucide-react';
import { cn, img } from '../../utils';
import LazyImage from '../common/LazyImage';
import RatingStars from './RatingStars';
import DiscountBadge from './DiscountBadge';
import QuantitySelector from './QuantitySelector';

const formatPrice = (value, currency = 'USD') => {
  try {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(value);
  } catch (e) {
    return `$${value}`;
  }
};

const ProductCard = ({
  product,
  onAddToCart,
  onToggleWishlist,
  onView,
  currency = 'USD',
  variant = 'default',
  className = '',
}) => {
  const [qty, setQty] = useState(1);
  const [added, setAdded] = useState(false);
  const {
    id,
    name = 'Untitled product',
    image = img.product,
    price = 0,
    compareAtPrice = 0,
    rating = 4.5,
    reviewCount = 0,
    discountPercent,
    badge,
  } = product || {};

  const handleAdd = () => {
    if (typeof onAddToCart === 'function') onAddToCart({ ...product, quantity: qty });
    setAdded(true);
    setTimeout(() => setAdded(false), 1500);
  };

  const discount = Number.isFinite(discountPercent)
    ? discountPercent
    : compareAtPrice > price && price > 0
      ? Math.round(((compareAtPrice - price) / compareAtPrice) * 100)
      : 0;

  return (
    <article
      className={cn(
        'group relative flex flex-col overflow-hidden rounded-2xl border bg-card text-card-foreground shadow-sm transition-all duration-200 hover:shadow-lg',
        className
      )}
    >
      <div className="relative aspect-[4/5] overflow-hidden bg-muted">
        <button
          type="button"
          onClick={() => typeof onView === 'function' && onView(product)}
          className="block h-full w-full"
          aria-label={`View ${name}`}
        >
          <LazyImage
            src={image}
            alt={name}
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
          />
        </button>
        {discount > 0 && (
          <div className="absolute left-3 top-3">
            <DiscountBadge discountPercent={discount} size="md" />
          </div>
        )}
        {typeof onToggleWishlist === 'function' && (
          <button
            type="button"
            onClick={() => onToggleWishlist(product)}
            aria-label={`Add ${name} to wishlist`}
            className="absolute right-3 top-3 flex h-9 w-9 items-center justify-center rounded-full bg-background/90 text-muted-foreground shadow-sm backdrop-blur transition-all duration-200 hover:bg-destructive hover:text-white focus:outline-none focus:ring-2 focus:ring-primary/40"
          >
            <Heart className="h-4 w-4" aria-hidden="true" />
          </button>
        )}
      </div>

      <div className="flex flex-1 flex-col gap-2 p-4">
        <div className="flex items-start justify-between gap-2">
          <h3 className="line-clamp-2 text-sm font-semibold text-foreground">
            <button
              type="button"
              onClick={() => typeof onView === 'function' && onView(product)}
              className="text-left transition-colors hover:text-primary"
            >
              {name}
            </button>
          </h3>
        </div>

        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          {badge && (
            <span className="rounded-full bg-primary/10 px-2 py-0.5 font-medium text-primary">
              {badge}
            </span>
          )}
        </div>

        {typeof rating === 'number' && (
          <RatingStars rating={rating} reviewCount={reviewCount} size="sm" showValue />
        )}

        <div className="mt-auto flex items-end justify-between gap-3 pt-1">
          <div className="space-y-0.5">
            {compareAtPrice > price && (
              <p className="text-xs text-muted-foreground line-through">
                {formatPrice(compareAtPrice, currency)}
              </p>
            )}
            <p className="text-lg font-bold text-foreground">{formatPrice(price, currency)}</p>
          </div>
          {typeof onAddToCart === 'function' && (
            <button
              type="button"
              onClick={handleAdd}
              className={cn(
                'flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary/40',
                added
                  ? 'bg-green-600 text-white'
                  : 'bg-primary text-primary-foreground hover:bg-primary/90'
              )}
            >
              <ShoppingCart className="h-4 w-4" aria-hidden="true" />
              {added ? 'Added' : 'Add'}
            </button>
          )}
        </div>

        {variant === 'withQty' && (
          <div className="flex justify-end">
            <QuantitySelector value={qty} onChange={setQty} size="sm" />
          </div>
        )}
      </div>
    </article>
  );
};

export default ProductCard;
