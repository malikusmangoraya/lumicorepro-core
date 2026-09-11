import React from 'react';
import { cn, getAnimationClass } from '../../utils';

const variants = {
  primary: 'bg-primary',
  success: 'bg-green-500',
  warning: 'bg-yellow-500',
  danger: 'bg-red-500',
  info: 'bg-blue-500',
};

const sizes = {
  xs: 'h-1',
  sm: 'h-1.5',
  md: 'h-2',
  lg: 'h-3',
  xl: 'h-4',
};

const Progress = React.forwardRef(
  (
    {
      value = 0,
      max = 100,
      variant = 'primary',
      size = 'md',
      showLabel = false,
      label,
      indeterminate = false,
      animate = 'none',
      onComplete,
      className = '',
      ...props
    },
    ref
  ) => {
    const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
    const prevRef = React.useRef(percentage);

    React.useEffect(() => {
      if (percentage >= 100 && prevRef.current < 100) {
        onComplete?.(value);
      }
      prevRef.current = percentage;
    }, [percentage, value, onComplete]);

    return (
      <div ref={ref} className={cn('w-full', getAnimationClass(animate), className)} {...props}>
        <div
          role="progressbar"
          aria-valuenow={indeterminate ? undefined : value}
          aria-valuemin={0}
          aria-valuemax={max}
          aria-label={label || 'Progress'}
          className={cn('w-full overflow-hidden rounded-full bg-muted', sizes[size])}
        >
          {indeterminate ? (
            <div
              className={cn(
                'h-full rounded-full animate-progress-indeterminate',
                variants[variant]
              )}
            />
          ) : (
            <div
              className={cn(
                'h-full rounded-full transition-all duration-500 ease-out',
                variants[variant]
              )}
              style={{ width: `${percentage}%` }}
            />
          )}
        </div>
        {showLabel && (
          <div className="mt-1.5 flex justify-between text-xs text-muted-foreground">
            <span>{label}</span>
            <span>{Math.round(percentage)}%</span>
          </div>
        )}
      </div>
    );
  }
);

Progress.displayName = 'Progress';

export default Progress;
