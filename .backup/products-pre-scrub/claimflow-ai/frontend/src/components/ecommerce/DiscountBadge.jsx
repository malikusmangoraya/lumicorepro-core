import React from 'react';
import { cn } from '../../utils';

const DiscountBadge = ({
  discountPercent = 0,
  compareAtPrice = 0,
  price = 0,
  label,
  size = 'md',
  className = '',
}) => {
  const computed = Number.isFinite(discountPercent)
    ? discountPercent
    : compareAtPrice > price && price > 0
      ? Math.round(((compareAtPrice - price) / compareAtPrice) * 100)
      : 0;

  const text = label || `${computed}% OFF`;
  const sizes = {
    sm: 'px-1.5 py-0.5 text-[10px]',
    md: 'px-2.5 py-1 text-xs',
    lg: 'px-3 py-1.5 text-sm',
  };

  if (computed <= 0) return null;

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full bg-destructive font-bold uppercase tracking-wide text-white shadow-sm',
        sizes[size] || sizes.md,
        className
      )}
    >
      {text}
    </span>
  );
};

export default DiscountBadge;
