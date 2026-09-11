/**
 * Shared shell for Phase 4 templates — simple, professional, animated.
 */

import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { cn, getAnimationClass } from '@/utils';
import { Badge } from '@/components/ui';

export default function TemplateShell({
  title,
  description,
  category,
  children,
  actions,
  className = '',
}) {
  return (
    <div className={cn('space-y-6 animate-page-enter', className)}>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className={getAnimationClass('fade-up')}>
          <div className="mb-3 flex items-center gap-3">
            <Link
              to="/templates"
              className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              Templates
            </Link>
            {category && (
              <Badge variant="outline" size="sm">
                {category}
              </Badge>
            )}
          </div>
          <h1 className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
            {title}
          </h1>
          {description && (
            <p className="mt-1.5 text-sm sm:text-base text-muted-foreground max-w-2xl">
              {description}
            </p>
          )}
        </div>
        {actions && (
          <div className={cn('flex flex-wrap gap-2', getAnimationClass('fade-up', 100))}>
            {actions}
          </div>
        )}
      </div>
      <div className={getAnimationClass('fade-up', 150)}>{children}</div>
    </div>
  );
}
