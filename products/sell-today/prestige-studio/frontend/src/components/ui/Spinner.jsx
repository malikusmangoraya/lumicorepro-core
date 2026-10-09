import React from 'react';
import { cn, getAnimationClass } from '../../utils';

const sizes = {
  xs: 'h-3 w-3 border-2',
  sm: 'h-4 w-4 border-2',
  md: 'h-6 w-6 border-2',
  lg: 'h-8 w-8 border-[3px]',
  xl: 'h-12 w-12 border-4',
};

const colors = {
  primary: 'border-primary/30 border-t-primary',
  white: 'border-white/30 border-t-white',
  muted: 'border-muted-foreground/30 border-t-muted-foreground',
};

const Spinner = ({
  size = 'md',
  color = 'primary',
  label = 'Loading...',
  className = '',
  ...props
}) => {
  return (
    <div
      role="status"
      aria-label={label}
      className={cn('inline-flex items-center justify-center', className)}
      {...props}
    >
      <span
        className={cn(sizes[size], colors[color], 'rounded-full animate-spin')}
        aria-hidden="true"
      />
      {label && <span className="sr-only">{label}</span>}
    </div>
  );
};

export default Spinner;
