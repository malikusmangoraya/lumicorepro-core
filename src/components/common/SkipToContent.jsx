import { cn } from '@/utils';

export default function SkipToContent({ className = '' }) {
  return (
    <a
      href="#main-content"
      className={cn(
        'sr-only focus:not-sr-only',
        'focus:fixed focus:top-4 focus:left-4 focus:z-[9999]',
        'focus:inline-flex focus:items-center focus:gap-2',
        'focus:rounded-lg focus:bg-primary focus:px-4 focus:py-2',
        'focus:text-sm focus:font-semibold focus:text-primary-foreground',
        'focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-primary/50',
        className
      )}
    >
      Skip to main content
    </a>
  );
}
