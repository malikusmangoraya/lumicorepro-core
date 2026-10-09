import React from 'react';
import { Star, StarHalf } from 'lucide-react';
import { cn } from '../../utils';

const RatingStars = ({
  rating = 0,
  max = 5,
  showValue = false,
  reviewCount = 0,
  size = 'md',
  className = '',
}) => {
  const sizes = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5',
  };
  const iconClass = sizes[size] || sizes.md;

  const renderStar = (index) => {
    const half = rating - index >= 0.5 && rating - index < 1;
    return half ? (
      <span key={index} className="relative inline-block">
        <Star className={cn(iconClass, 'text-muted-foreground/40')} aria-hidden="true" />
        <span className="absolute inset-0 overflow-hidden" style={{ width: '50%' }}>
          <Star className={cn(iconClass, 'fill-amber-400 text-amber-400')} aria-hidden="true" />
        </span>
      </span>
    ) : (
      <Star
        key={index}
        className={cn(
          iconClass,
          rating - index >= 1 ? 'fill-amber-400 text-amber-400' : 'text-muted-foreground/40'
        )}
        aria-hidden="true"
      />
    );
  };

  const label = `${rating} out of ${max} stars`;

  return (
    <div
      className={cn('flex items-center gap-1.5', className)}
      role="img"
      aria-label={label}
      title={label}
    >
      <div className="flex items-center gap-0.5">
        {Array.from({ length: max }, (_, i) => renderStar(i))}
      </div>
      {showValue && (
        <span className="text-xs font-medium text-muted-foreground">
          {rating.toFixed(1)}
          {reviewCount > 0 && ` (${reviewCount})`}
        </span>
      )}
    </div>
  );
};

export default RatingStars;
