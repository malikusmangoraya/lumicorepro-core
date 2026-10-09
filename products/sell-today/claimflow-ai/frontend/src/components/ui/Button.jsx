import React from 'react';
import { Loader } from 'lucide-react';
import { cn, getAnimationClass } from '../../utils';

const variants = {
  primary: 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm',
  secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
  danger: 'bg-destructive text-destructive-foreground hover:bg-destructive/90 shadow-sm',
  success: 'bg-green-600 text-white hover:bg-green-700 shadow-sm',
  warning: 'bg-amber-500 text-white hover:bg-amber-600 shadow-sm',
  info: 'bg-sky-500 text-white hover:bg-sky-600 shadow-sm',
  outline: 'border border-border bg-transparent hover:bg-muted text-foreground',
  ghost: 'bg-transparent hover:bg-muted text-foreground',
  link: 'bg-transparent text-primary underline-offset-4 hover:underline p-0 h-auto',
};

const sizes = {
  xs: 'h-7 px-2.5 text-xs',
  sm: 'h-8 px-3 text-sm',
  md: 'h-10 px-4 text-sm',
  lg: 'h-11 px-6 text-base',
  xl: 'h-12 px-8 text-lg',
};

const Button = React.forwardRef(
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
      onMouseEnter,
      onMouseLeave,
      onFocus,
      onBlur,
      ...props
    },
    ref
  ) => {
    const classes = cn(
      'inline-flex items-center justify-center gap-2 rounded-lg font-medium',
      'transition-all duration-200',
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
      'disabled:opacity-50 disabled:pointer-events-none active:scale-[0.98]',
      variants[variant],
      sizes[size],
      fullWidth && 'w-full',
      getAnimationClass(animate, animationDelay),
      className
    );

    return (
      <button
        ref={ref}
        type={type}
        className={classes}
        disabled={disabled || loading}
        aria-busy={loading}
        aria-disabled={disabled || loading}
        onClick={onClick}
        onMouseEnter={onMouseEnter}
        onMouseLeave={onMouseLeave}
        onFocus={onFocus}
        onBlur={onBlur}
        {...props}
      >
        {loading ? (
          <Loader className="h-4 w-4 animate-spin" aria-hidden="true" />
        ) : (
          LeftIcon && <LeftIcon className="h-4 w-4" aria-hidden="true" />
        )}
        {children}
        {!loading && RightIcon && <RightIcon className="h-4 w-4" aria-hidden="true" />}
      </button>
    );
  }
);

Button.displayName = 'Button';

export { Button };
export default Button;
