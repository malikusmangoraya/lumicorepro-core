import React from 'react';
import { cn } from '../../utils';

const sizes = {
  sm: 'px-3 py-1.5 text-[10px]',
  md: 'px-5 py-2.5 text-xs',
  lg: 'px-7 py-3.5 text-sm',
};

const variants = {
  primary: 'bg-primary text-primary-foreground',
  secondary: 'bg-muted text-muted-foreground',
  ghost: 'bg-transparent text-foreground hover:bg-muted',
};

const PixelButton = React.forwardRef(
  (
    {
      children,
      size = 'md',
      variant = 'primary',
      disabled = false,
      className = '',
      type = 'button',
      ...props
    },
    ref
  ) => (
    <button
      ref={ref}
      type={type}
      disabled={disabled}
      className={cn(
        'relative font-mono font-bold uppercase tracking-[0.2em] image-rendering-pixelated',
        'border-2 border-foreground/90 shadow-[4px_4px_0_0_currentColor]',
        'transition-transform duration-75 ease-out',
        'hover:-translate-x-[2px] hover:-translate-y-[2px] hover:shadow-[6px_6px_0_0_currentColor]',
        'active:translate-x-0 active:translate-y-0 active:shadow-[2px_2px_0_0_currentColor]',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
        variants[variant],
        sizes[size],
        disabled &&
          'cursor-not-allowed opacity-60 shadow-none hover:translate-x-0 hover:translate-y-0 hover:shadow-none',
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
);

PixelButton.displayName = 'PixelButton';

export default PixelButton;
