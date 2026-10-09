import React from 'react';
import Tooltip from './Tooltip';
import { cn, getAnimationClass } from '../../utils';

const variants = {
  primary: 'bg-primary text-primary-foreground hover:bg-primary/90',
  secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
  ghost: 'bg-transparent hover:bg-muted text-foreground',
  outline: 'border border-border bg-transparent hover:bg-muted text-foreground',
  danger: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
};

const sizes = {
  sm: 'h-8 w-8',
  md: 'h-10 w-10',
  lg: 'h-12 w-12',
};

const iconSizes = {
  sm: 'h-4 w-4',
  md: 'h-5 w-5',
  lg: 'h-6 w-6',
};

const IconButton = React.forwardRef(
  (
    {
      icon: Icon,
      label,
      variant = 'ghost',
      size = 'md',
      disabled = false,
      loading = false,
      tooltip,
      animate = 'none',
      animationDelay = 0,
      className = '',
      onClick,
      onMouseEnter,
      onMouseLeave,
      ...props
    },
    ref
  ) => {
    const button = (
      <button
        ref={ref}
        type="button"
        className={cn(
          'inline-flex items-center justify-center rounded-lg transition-all duration-200',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
          'disabled:opacity-50 disabled:pointer-events-none active:scale-95',
          variants[variant],
          sizes[size],
          getAnimationClass(animate, animationDelay),
          className
        )}
        disabled={disabled || loading}
        aria-label={label}
        aria-busy={loading}
        onClick={onClick}
        onMouseEnter={onMouseEnter}
        onMouseLeave={onMouseLeave}
        {...props}
      >
        {loading ? (
          <span
            className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"
            aria-hidden="true"
          />
        ) : (
          Icon && <Icon className={iconSizes[size]} aria-hidden="true" />
        )}
      </button>
    );

    if (tooltip) {
      return <Tooltip content={tooltip}>{button}</Tooltip>;
    }

    return button;
  }
);

IconButton.displayName = 'IconButton';

export default IconButton;
