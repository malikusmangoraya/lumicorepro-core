import React from 'react';
import { cn } from '../../utils';

const variants = {
  text: 'h-4 w-full rounded',
  circle: 'h-10 w-10 rounded-full',
  rect: 'h-20 w-full rounded-lg',
  card: 'h-40 w-full rounded-xl',
  button: 'h-10 w-24 rounded-lg',
  avatar: 'h-12 w-12 rounded-full',
  image: 'h-48 w-full rounded-lg',
};

const Skeleton = React.forwardRef(
  ({ className = '', variant = 'text', shimmer = true, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'bg-muted',
          shimmer ? 'animate-shimmer' : 'animate-pulse',
          variants[variant],
          className
        )}
        role="status"
        aria-label="Loading..."
        {...props}
      >
        <span className="sr-only">Loading...</span>
      </div>
    );
  }
);

Skeleton.displayName = 'Skeleton';

export default Skeleton;
