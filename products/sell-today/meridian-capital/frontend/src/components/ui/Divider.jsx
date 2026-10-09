import React from 'react';
import { cn } from '../../utils';

const Divider = React.forwardRef(
  ({ orientation = 'horizontal', variant = 'solid', label, className = '', ...props }, ref) => {
    const variants = {
      solid: 'border-border',
      dashed: 'border-dashed border-border',
      dotted: 'border-dotted border-border',
    };

    if (orientation === 'vertical') {
      return (
        <div
          ref={ref}
          className={cn('inline-block h-full w-px border-l', variants[variant], className)}
          role="separator"
          aria-orientation="vertical"
          {...props}
        />
      );
    }

    if (label) {
      return (
        <div
          ref={ref}
          className={cn('flex items-center gap-3', className)}
          role="separator"
          {...props}
        >
          <div className={cn('flex-1 border-t', variants[variant])} />
          <span className="text-xs font-medium text-muted-foreground whitespace-nowrap">
            {label}
          </span>
          <div className={cn('flex-1 border-t', variants[variant])} />
        </div>
      );
    }

    return (
      <div
        ref={ref}
        className={cn('border-t', variants[variant], className)}
        role="separator"
        {...props}
      />
    );
  }
);

Divider.displayName = 'Divider';

export default Divider;
