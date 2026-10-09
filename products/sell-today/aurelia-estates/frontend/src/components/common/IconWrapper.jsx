import React from 'react';
import { cn } from '../../utils';

const IconWrapper = ({
  icon: Icon,
  size = 'md',
  variant = 'primary',
  className = '',
  ...iconProps
}) => {
  const container = {
    xs: 'h-6 w-6',
    sm: 'h-9 w-9',
    md: 'h-12 w-12',
    lg: 'h-16 w-16',
  };
  const icon = {
    xs: 'h-3 w-3',
    sm: 'h-4 w-4',
    md: 'h-5 w-5',
    lg: 'h-7 w-7',
  };
  const tones = {
    primary: 'bg-primary/10 text-primary',
    secondary: 'bg-secondary/80 text-secondary-foreground',
    success: 'bg-green-600/10 text-green-600 dark:text-green-400',
    danger: 'bg-destructive/10 text-destructive',
    warning: 'bg-amber-500/10 text-amber-600 dark:text-amber-400',
    ghost: 'bg-muted text-foreground',
  };

  return (
    <span
      className={cn(
        'inline-flex shrink-0 items-center justify-center rounded-xl',
        container[size],
        tones[variant] || tones.primary,
        className
      )}
      aria-hidden="true"
    >
      {Icon && <Icon className={icon[size]} {...iconProps} />}
    </span>
  );
};

export default IconWrapper;
export { IconWrapper as IconWrapper };
