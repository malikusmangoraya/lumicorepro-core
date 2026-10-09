import React from 'react';
import { cn } from '../../utils';

const sizes = {
  sm: 'px-4 py-2 text-xs rounded-xl',
  md: 'px-6 py-3 text-sm rounded-2xl',
  lg: 'px-8 py-4 text-base rounded-2xl',
};

const NeumorphButton = React.forwardRef(
  (
    {
      children,
      size = 'md',
      pressed = false,
      accent = false,
      disabled = false,
      className = '',
      type = 'button',
      'aria-pressed': ariaPressed,
      ...props
    },
    ref
  ) => {
    const base =
      'font-medium transition-shadow duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring';
    const tone = accent ? 'bg-accent text-accent-foreground' : 'bg-muted text-muted-foreground';
    const elevation = pressed
      ? 'shadow-[inset_4px_4px_8px_rgba(0,0,0,0.15),inset_-4px_-4px_8px_rgba(255,255,255,0.05)]'
      : 'shadow-[6px_6px_12px_rgba(0,0,0,0.16),-6px_-6px_12px_rgba(255,255,255,0.06)] hover:shadow-[4px_4px_10px_rgba(0,0,0,0.18),-4px_-4px_10px_rgba(255,255,255,0.07)]';

    return (
      <button
        ref={ref}
        type={type}
        disabled={disabled}
        aria-pressed={pressed ? true : ariaPressed}
        className={cn(
          base,
          tone,
          sizes[size],
          elevation,
          disabled && 'cursor-not-allowed opacity-60',
          className
        )}
        {...props}
      >
        {children}
      </button>
    );
  }
);

NeumorphButton.displayName = 'NeumorphButton';

export default NeumorphButton;
