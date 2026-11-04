'use client';

import { Columns3 } from 'lucide-react';
import { useSite, SITE_LIMITS } from '@/components/providers/site-provider';
import { cn } from '@/lib/utils';

export function CompareButton({
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
  const { isCompared, toggleCompare, notify, compare } = useSite();
  const active = isCompared(slug);

  const onClick = () => {
    const added = toggleCompare(slug);
    if (!added) {
      notify(`You can compare up to ${SITE_LIMITS.compare} cars at a time. Remove one first.`);
      return;
    }
    notify(active ? `Removed ${title} from compare` : `Added ${title} to compare`);
  };

  const label = active ? `Remove ${title} from compare` : `Compare ${title}`;

  if (variant === 'full') {
    return (
      <button
        type="button"
        onClick={onClick}
        aria-pressed={active}
        className={cn(
          'inline-flex h-11 items-center justify-center gap-2 rounded-control border px-4 text-sm font-semibold transition-colors',
          active
            ? 'border-primary/60 bg-primary/10 text-accent'
            : 'border-line text-heading hover:border-primary/60 hover:bg-white/5',
          className,
        )}
      >
        <Columns3 className="size-4" aria-hidden="true" />
        {active ? `In compare (${compare.length})` : 'Compare'}
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      aria-label={label}
      title={active ? 'Remove from compare' : 'Add to compare'}
      className={cn(
        'inline-flex size-9 items-center justify-center rounded-full border backdrop-blur transition-colors',
        active
          ? 'border-primary/60 bg-primary/20 text-accent'
          : 'border-white/15 bg-canvas/70 text-body/80 hover:border-primary/60 hover:text-heading',
        className,
      )}
    >
      <Columns3 className="size-4" aria-hidden="true" />
    </button>
  );
}
