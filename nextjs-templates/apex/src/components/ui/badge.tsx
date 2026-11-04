import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

type Tone = 'neutral' | 'primary' | 'success' | 'warning' | 'danger';

const tones: Record<Tone, string> = {
  neutral: 'border-line bg-white/5 text-body/85',
  primary: 'border-primary/40 bg-primary/10 text-accent',
  success: 'border-emerald-500/35 bg-emerald-500/10 text-emerald-300',
  warning: 'border-amber-500/35 bg-amber-500/10 text-amber-300',
  danger: 'border-red-500/35 bg-red-500/10 text-red-300',
};

export function Badge({
  tone = 'neutral',
  children,
  className,
}: {
  tone?: Tone;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[0.7rem] font-semibold uppercase tracking-wide',
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
