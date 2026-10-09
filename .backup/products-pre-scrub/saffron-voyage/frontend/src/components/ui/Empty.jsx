import React from 'react';
import { Inbox } from 'lucide-react';
import { cn, getAnimationClass } from '../../utils';

const Empty = React.forwardRef(
  (
    {
      title = 'No data available',
      description,
      icon: Icon = Inbox,
      action,
      onAction,
      animate = 'fade-up',
      className = '',
      ...props
    },
    ref
  ) => {
    return (
      <div
        ref={ref}
        className={cn(
          'flex flex-col items-center justify-center py-12 px-4 text-center',
          getAnimationClass(animate),
          className
        )}
        {...props}
      >
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted mb-4 animate-scale-in">
          <Icon className="h-8 w-8 text-muted-foreground" aria-hidden="true" />
        </div>
        <h3 className="text-base font-semibold text-foreground">{title}</h3>
        {description && (
          <p className="mt-1 text-sm text-muted-foreground max-w-sm">{description}</p>
        )}
        {(action || onAction) && (
          <div className="mt-5" onClick={onAction}>
            {action}
          </div>
        )}
      </div>
    );
  }
);

Empty.displayName = 'Empty';

export default Empty;
