import React from 'react';
import { cn, img } from '../../utils';
import ProductCard from './ProductCard';

const ProductGrid = ({
  products,
  columns = 4,
  onAddToCart,
  onToggleWishlist,
  onView,
  currency = 'USD',
  title,
  subtitle,
  className = '',
}) => {
  const colClass =
    {
      2: 'sm:grid-cols-2',
      3: 'sm:grid-cols-2 lg:grid-cols-3',
      4: 'sm:grid-cols-2 lg:grid-cols-4',
      5: 'sm:grid-cols-2 lg:grid-cols-5',
    }[columns] || 'sm:grid-cols-2 lg:grid-cols-4';

  const items =
    products && products.length > 0
      ? products
      : Array.from({ length: 8 }, (_, i) => ({
          id: `demo-${i}`,
          name: 'Premium product',
          price: 49 + i * 5,
          image: img.product,
          rating: 4.5,
        }));

  return (
    <section className={cn('w-full', className)}>
      {(title || subtitle) && (
        <div className="mb-6 space-y-1 text-center">
          {title && (
            <h2 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
              {title}
            </h2>
          )}
          {subtitle && <p className="text-sm text-muted-foreground sm:text-base">{subtitle}</p>}
        </div>
      )}
      <div className={cn('grid grid-cols-1 gap-5', colClass)}>
        {items.map((product) => (
          <ProductCard
            key={product.id}
            product={product}
            onAddToCart={onAddToCart}
            onToggleWishlist={onToggleWishlist}
            onView={onView}
            currency={currency}
          />
        ))}
      </div>
    </section>
  );
};

export default ProductGrid;
