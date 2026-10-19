import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../utils';

const variants = {
  primary: 'bg-primary/20 text-primary border-primary/30 hover:bg-primary/30',
  secondary: 'bg-secondary/20 text-secondary-foreground border-border/30 hover:bg-secondary/30',
  danger: 'bg-destructive/20 text-destructive border-destructive/30 hover:bg-destructive/30',
  success: 'bg-green-500/20 text-green-500 border-green-500/30 hover:bg-green-500/30',
  outline: 'bg-transparent text-foreground border-border/50 hover:bg-muted/50',
  ghost: 'bg-transparent text-foreground border-transparent hover:bg-muted/30',
};

const sizes = {
  xs: 'h-7 px-2.5 text-xs',
  sm: 'h-8 px-3 text-sm',
  md: 'h-10 px-4 text-sm',
  lg: 'h-11 px-6 text-base',
  xl: 'h-12 px-8 text-lg',
};

const GlassButton = React.forwardRef(
  (
    {
      children,
      variant = 'primary',
      size = 'md',
      loading = false,
      disabled = false,
      fullWidth = false,
      leftIcon: LeftIcon,
      rightIcon: RightIcon,
      animate = 'none',
      animationDelay = 0,
      className = '',
      type = 'button',
      onClick,
      ...props
    },
    ref
  ) => {
    const classes = cn(
      'inline-flex items-center justify-center gap-2 rounded-xl font-medium',
      'backdrop-blur-xl border transition-all duration-200',
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
      'disabled:opacity-50 disabled:pointer-events-none active:scale-[0.98]',
      variants[variant],
      sizes[size],
      fullWidth && 'w-full',
      className
    );

    return (
      <motion.button
        ref={ref}
        type={type}
        className={classes}
        disabled={disabled || loading}
        aria-busy={loading}
        aria-disabled={disabled || loading}
        onClick={onClick}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        {...props}
      >
        {loading ? (
          <motion.div
            className="h-4 w-4"
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          >
            <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" aria-hidden="true">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="3"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          </motion.div>
        ) : (
          LeftIcon &&
          (typeof LeftIcon === 'function' || LeftIcon?.prototype?.isReactComponent ? (
            <LeftIcon className="h-4 w-4" aria-hidden="true" />
          ) : (
            LeftIcon
          ))
        )}
        {children}
        {!loading && RightIcon &&
          (typeof RightIcon === 'function' || RightIcon?.prototype?.isReactComponent ? (
            <RightIcon className="h-4 w-4" aria-hidden="true" />
          ) : (
            RightIcon
          ))}
      </motion.button>
    );
  }
);

GlassButton.displayName = 'GlassButton';

export default GlassButton;