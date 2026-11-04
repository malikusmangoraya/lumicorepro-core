import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

export function Section({
  children,
  className,
  id,
}: {
  children: ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <section id={id} className={cn('mx-auto w-full max-w-6xl px-4 py-16 sm:px-6 sm:py-20', className)}>
      {children}
    </section>
  );
}

export function SectionHeading({
  eyebrow,
  title,
  description,
  align = 'left',
  as: Heading = 'h2',
  className,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  align?: 'left' | 'center';
  /** Use h1 for the title of a page; h2 for a section inside one. */
  as?: 'h1' | 'h2' | 'h3';
  className?: string;
}) {
  return (
    <div className={cn('max-w-2xl space-y-3', align === 'center' && 'mx-auto text-center', className)}>
      {eyebrow && <p className="section-eyebrow">{eyebrow}</p>}
      <Heading className="text-balance text-3xl font-700 leading-tight text-heading sm:text-4xl">
        {title}
      </Heading>
      {description && (
        <p className="text-pretty text-base leading-relaxed text-muted">{description}</p>
      )}
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="rounded-panel border border-dashed border-line bg-surface/40 px-6 py-16 text-center">
      <h3 className="text-lg font-600 text-heading">{title}</h3>
      <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-muted">{description}</p>
      {action && <div className="mt-6 flex justify-center">{action}</div>}
    </div>
  );
}

export function ErrorState({
  title = 'Something went wrong',
  description,
  action,
}: {
  title?: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div role="alert" className="rounded-panel border border-red-500/30 bg-red-500/5 px-6 py-10 text-center">
      <h3 className="text-lg font-600 text-heading">{title}</h3>
      <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-muted">{description}</p>
      {action && <div className="mt-5 flex justify-center">{action}</div>}
    </div>
  );
}
