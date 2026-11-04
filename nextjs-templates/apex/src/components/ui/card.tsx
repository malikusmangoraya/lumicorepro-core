import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

/** The panel surface used for every card on the site. */
export function Panel({
  children,
  className,
  as: Tag = 'div',
}: {
  children: ReactNode;
  className?: string;
  as?: 'div' | 'article' | 'li' | 'section';
}) {
  return (
    <Tag
      className={cn(
        'rounded-panel border border-line bg-surface/70 shadow-panel backdrop-blur-[2px]',
        className,
      )}
    >
      {children}
    </Tag>
  );
}

export function PanelHeader({
  eyebrow,
  title,
  description,
  className,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  className?: string;
}) {
  return (
    <div className={cn('space-y-2', className)}>
      {eyebrow && <p className="section-eyebrow">{eyebrow}</p>}
      <h2 className="text-balance text-xl font-700 text-heading sm:text-2xl">{title}</h2>
      {description && <p className="text-sm leading-relaxed text-muted">{description}</p>}
    </div>
  );
}

export function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div className="rounded-panel border border-line/80 bg-surface/50 px-4 py-5 text-center">
      <p className="font-display text-2xl font-700 text-heading sm:text-3xl">{value}</p>
      <p className="mt-1 text-xs uppercase tracking-[0.14em] text-muted">{label}</p>
    </div>
  );
}
