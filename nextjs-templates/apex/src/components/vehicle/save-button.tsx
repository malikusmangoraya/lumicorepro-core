'use client';

import { Heart } from 'lucide-react';
import { useSite } from '@/components/providers/site-provider';
import { cn } from '@/lib/utils';

export function SaveButton({
  slug,
  title,
  variant = 'icon',
  className,
}: {
  slug: string;
  title: string;
  variant?: 'icon' | 'full';
  className?: string;
}) {
  const { isSaved, toggleSaved, notify } = useSite();
  const saved = isSaved(slug);

  const onClick = () => {
    toggleSaved(slug);
    notify(saved ? `Removed ${title} from saved` : `Saved ${title}`);
  };

  if (variant === 'full') {
    return (
      <button
        type="button"
        onClick={onClick}
        aria-pressed={saved}
        className={cn(
          'inline-flex h-11 items-center justify-center gap-2 rounded-control border px-4 text-sm font-semibold transition-colors',
          saved
            ? 'border-primary/60 bg-primary/10 text-accent'
            : 'border-line text-heading hover:border-primary/60 hover:bg-white/5',
          className,
        )}
      >
        <Heart className={cn('size-4', saved && 'fill-current')} aria-hidden="true" />
        {saved ? 'Saved' : 'Save'}
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={saved}
      aria-label={saved ? `Remove ${title} from saved` : `Save ${title}`}
      title={saved ? 'Remove from saved' : 'Save this car'}
      className={cn(
        'inline-flex size-9 items-center justify-center rounded-full border backdrop-blur transition-colors',
        saved
          ? 'border-primary/60 bg-primary/20 text-accent'
          : 'border-white/15 bg-canvas/70 text-body/80 hover:border-primary/60 hover:text-heading',
        className,
      )}
    >
      <Heart className={cn('size-4', saved && 'fill-current')} aria-hidden="true" />
    </button>
  );
}
