import React from 'react';
import { Link } from 'react-router-dom';
import { cn } from '../../utils';
import { ChevronRight, Home } from 'lucide-react';

const Breadcrumb = React.forwardRef(
  (
    {
      items = [],
      separator = ChevronRight,
      className = '',
      maxItems = 5,
      showHome = true,
      homeLabel = 'Home',
      homeHref = '/',
      ...props
    },
    ref
  ) => {
    const displayItems = items.length > maxItems
      ? [
          items[0],
          { label: '...', disabled: true },
          ...items.slice(-(maxItems - 2)),
        ]
      : items;

    return (
      <nav
        ref={ref}
        aria-label="Breadcrumb"
        className={cn('flex flex-wrap items-center gap-1.5 text-sm', className)}
        {...props}
      >
        <ol className="flex flex-wrap items-center gap-1.5" role="list">
          {showHome && (
            <li>
              <Link
                to={homeHref}
                className="flex items-center gap-1.5 text-muted-foreground hover:text-foreground transition-colors"
                aria-label={homeLabel}
              >
                <Home className="h-4 w-4" aria-hidden="true" />
                <span className="hidden sm:inline">{homeLabel}</span>
              </Link>
              <separator className="h-4 w-4 text-muted-foreground/50 flex-shrink-0" aria-hidden="true" />
            </li>
          )}
          {displayItems.map((item, index) => {
            const isLast = index === displayItems.length - 1;
            const isDisabled = item.disabled;

            return (
              <li key={item.href || item.label || index} className="flex items-center gap-1.5">
                {isDisabled ? (
                  <span className="text-muted-foreground/50" aria-hidden="true">
                    {item.label}
                  </span>
                ) : item.href ? (
                  <Link
                    to={item.href}
                    className={cn(
                      'flex items-center gap-1.5 text-muted-foreground hover:text-foreground transition-colors',
                      isLast && 'font-medium text-foreground'
                    )}
                    aria-current={isLast ? 'page' : undefined}
                  >
                    {item.icon && <item.icon className="h-4 w-4" aria-hidden="true" />}
                    <span>{item.label}</span>
                  </Link>
                ) : (
                  <span
                    className={cn(
                      'flex items-center gap-1.5',
                      isLast ? 'font-medium text-foreground' : 'text-muted-foreground'
                    )}
                    aria-current={isLast ? 'page' : undefined}
                  >
                    {item.icon && <item.icon className="h-4 w-4" aria-hidden="true" />}
                    <span>{item.label}</span>
                  </span>
                )}
                {!isLast && (
                  <separator className="h-4 w-4 text-muted-foreground/50 flex-shrink-0" aria-hidden="true" />
                )}
              </li>
            );
          })}
        </ol>
      </nav>
    );
  }
);

Breadcrumb.displayName = 'Breadcrumb';

export default Breadcrumb;