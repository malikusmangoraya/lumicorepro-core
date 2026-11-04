import { Star } from 'lucide-react';
import { cn } from '@/lib/utils';

export function Stars({ rating, size = 14 }: { rating: number; size?: number }) {
  return (
    <span className="inline-flex items-center gap-0.5" aria-label={`${rating} out of 5`}>
      {[1, 2, 3, 4, 5].map((star) => (
        <Star
          key={star}
          style={{ width: size, height: size }}
          className={cn(
            star <= Math.round(rating) ? 'fill-amber-300 text-amber-300' : 'text-line',
          )}
          aria-hidden="true"
        />
      ))}
    </span>
  );
}
