import React from 'react';
import { ChevronRight, Home } from 'lucide-react';
import { cn, getAnimationClass } from '../../utils';

const Breadcrumb = ({
  items = [],
  separator = 'chevron',
  showHome = true,
  homeLabel = 'Home',
  homeHref = '/',
  onItemClick,
  onHomeClick,
  animate = 'none',
  className = '',
  itemClassName = '',
  ...props
}) => {
  const Separator = () => {
    if (separator === 'slash') {
      return (
        <span className="mx-2 text-muted-foreground" aria-hidden="true">
          /
        </span>
      );
    }
    if (separator === 'dot') {
      return (
        <span className="mx-2 text-muted-foreground" aria-hidden="true">
          •
        </span>
      );
    }
    return <ChevronRight className="mx-1.5 h-4 w-4 text-muted-foreground" aria-hidden="true" />;
  };

  return (
    <nav
      className={cn('flex items-center text-sm', getAnimationClass(animate), className)}
      aria-label="Breadcrumb"
      {...props}
    >
      <ol className="flex items-center flex-wrap gap-0">
        {showHome && (
          <li className="flex items-center">
            <a
              href={homeHref}
              onClick={(e) => onHomeClick?.(e)}
              className="flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors"
            >
              <Home className="h-4 w-4" aria-hidden="true" />
              <span className="sr-only">{homeLabel}</span>
            </a>
            <Separator />
          </li>
        )}
        {items.map((item, index) => {
          const isLast = index === items.length - 1;
          return (
            <li key={`${item.label}-${index}`} className="flex items-center">
              {item.href && !isLast ? (
                <a
                  href={item.href}
                  onClick={(e) => onItemClick?.(item, index, e)}
                  className={cn(
                    'text-muted-foreground hover:text-foreground transition-colors',
                    itemClassName
                  )}
                >
                  {item.label}
                </a>
              ) : (
                <span
                  className={cn('font-medium text-foreground', itemClassName)}
                  aria-current={isLast ? 'page' : undefined}
                >
                  {item.label}
                </span>
              )}
              {!isLast && <Separator />}
            </li>
          );
        })}
      </ol>
    </nav>
  );
};

export default Breadcrumb;
