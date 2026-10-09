import React, { useState, useCallback, useMemo } from 'react';
import { MapPin, BedDouble, Bath, Square, Heart, Eye, ArrowRight, Sparkles, Filter } from 'lucide-react';
import { cn } from '@/utils';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import IconButton from '@/components/ui/IconButton';
import RatingStars from '@/components/ecommerce/RatingStars';
import Reveal from '@/components/motion/Reveal';
import LazyImage from '@/components/common/LazyImage';
import IconWrapper from '@/components/common/IconWrapper';
import Grid from '@/components/common/Grid';

export default function ProductGrid({
  products = [],
  columns = 3,
  onAddToCart,
  onToggleWishlist,
  onView,
  currency = 'USD',
  title = 'Featured Properties',
  subtitle = 'Handpicked residences curated for discerning buyers',
  className,
}) {
  const [wishlist, setWishlist] = useState(() => new Set());
  const [hoveredId, setHoveredId] = useState(null);

  const colClass = useMemo(() => {
    const map = { 1: 'sm:grid-cols-1', 2: 'sm:grid-cols-2', 3: 'sm:grid-cols-2 lg:grid-cols-3', 4: 'sm:grid-cols-2 lg:grid-cols-4' };
    return map[columns] || map[3];
  }, [columns]);

  const handleWishlist = useCallback((id) => {
    setWishlist((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
    onToggleWishlist?.(id);
  }, [onToggleWishlist]);

  const handleView = useCallback((product) => {
    onView?.(product);
  }, [onView]);

  const formatPrice = useCallback((price) => {
    if (!price) return '';
    return new Intl.NumberFormat('en-US', { style: 'currency', currency, maximumFractionDigits: 0 }).format(price);
  }, [currency]);

  if (!products.length) return null;

  return (
    <section className={cn('py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto', className)} aria-labelledby="product-grid-heading">
      <Reveal direction="up">
        <div className="text-center mb-12">
          <Badge variant="info" size="sm" className="mb-4">
            <Sparkles className="w-3.5 h-3.5 mr-1.5" aria-hidden="true" />
            Curated Selection
          </Badge>
          <h2 id="product-grid-heading" className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-foreground">
            {title.split(' ').slice(0, -1).join(' ')}{' '}
            <span className="bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
              {title.split(' ').slice(-1)}
            </span>
          </h2>
          {subtitle && (
            <p className="mt-3 text-muted-foreground text-base sm:text-lg max-w-2xl mx-auto">{subtitle}</p>
          )}
        </div>
      </Reveal>

      <div className={cn('grid grid-cols-1 gap-6 lg:gap-8', colClass)}>
        {products.map((product, i) => {
          const isWishlisted = wishlist.has(product.id);
          const isHovered = hoveredId === product.id;

          return (
            <Reveal key={product.id} delay={i * 80} direction="up">
              <Card
                hoverable
                className={cn(
                  'group relative overflow-hidden rounded-2xl border border-border/60 bg-card shadow-sm',
                  'transition-all duration-300 hover:shadow-xl hover:-translate-y-1',
                  isHovered && 'ring-1 ring-primary/30'
                )}
                onMouseEnter={() => setHoveredId(product.id)}
                onMouseLeave={() => setHoveredId(null)}
              >
                {/* Image */}
                <div className="relative aspect-[4/3] overflow-hidden rounded-t-2xl">
                  <LazyImage
                    src={product.image}
                    alt={product.name || 'Property listing'}
                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                    width={800}
                    height={600}
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                  {/* Badges */}
                  <div className="absolute top-3 left-3 flex flex-col gap-1.5">
                    {product.badge && (
                      <Badge variant="success" size="sm">{product.badge}</Badge>
                    )}
                    {product.type && (
                      <Badge variant="outline" size="sm" className="backdrop-blur-sm bg-background/60">
                        {product.type}
                      </Badge>
                    )}
                  </div>

                  {/* Wishlist */}
                  <IconButton
                    icon={Heart}
                    label={isWishlisted ? 'Remove from wishlist' : 'Add to wishlist'}
                    variant="ghost"
                    size="sm"
                    className={cn(
                      'absolute top-3 right-3 backdrop-blur-sm bg-background/60 rounded-full',
                      isWishlisted && 'text-danger [&_svg]:fill-current'
                    )}
                    onClick={(e) => { e.stopPropagation(); handleWishlist(product.id); }}
                  />
                </div>

                {/* Content */}
                <div className="p-5">
                  <div className="flex items-start justify-between gap-2 mb-2">
                                        <h3 className="font-semibold text-lg text-foreground leading-snug line-clamp-2">
                      {product.name}
                    </h3>
                    {product.price ? (
                      <span className="shrink-0 text-sm font-semibold text-primary">
                        {formatPrice(product.price)}
                      </span>
                    ) : null}
                  </div>

                  {product.location && (
                    <p className="flex items-center gap-1.5 text-sm text-muted-foreground">
                      <MapPin className="w-4 h-4 shrink-0" aria-hidden="true" />
                      <span className="truncate">{product.location}</span>
                    </p>
                  )}

                  {product.specs && (
                    <ul className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
                      {product.specs.beds != null && (
                        <li className="flex items-center gap-1.5">
                          <BedDouble className="w-4 h-4" aria-hidden="true" />
                          {product.specs.beds} {product.specs.beds === 1 ? 'bed' : 'beds'}
                        </li>
                      )}
                      {product.specs.baths != null && (
                        <li className="flex items-center gap-1.5">
                          <Bath className="w-4 h-4" aria-hidden="true" />
                          {product.specs.baths} {product.specs.baths === 1 ? 'bath' : 'baths'}
                        </li>
                      )}
                      {product.specs.area && (
                        <li className="flex items-center gap-1.5">
                          <Square className="w-4 h-4" aria-hidden="true" />
                          {product.specs.area}
                        </li>
                      )}
                    </ul>
                  )}

                  {product.rating ? (
                    <div className="mt-3">
                      <RatingStars
                        rating={product.rating}
                        size="sm"
                        showValue
                        reviewCount={product.reviewCount}
                      />
                    </div>
                  ) : null}
                </div>

                <div className="flex items-center gap-2 px-5 pb-5">
                  <Button
                    variant="primary"
                    className="flex-1"
                    onClick={() => handleView(product)}
                  >
                    <Eye className="mr-2 h-4 w-4" aria-hidden="true" />
                    View residence
                  </Button>
                  {onAddToCart && (
                    <Button
                      variant="outline"
                      onClick={() => onAddToCart(product)}
                      aria-label={`Enquire about ${product.name}`}
                    >
                      <ArrowRight className="h-4 w-4" aria-hidden="true" />
                    </Button>
                  )}
                </div>
              </Card>
            </Reveal>
          );
        })}
      </div>
    </section>
  );
}
