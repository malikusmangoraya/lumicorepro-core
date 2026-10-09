import React, { useState } from 'react';
import { cn, getAnimationClass } from '../../utils';

const sizes = {
  xs: 'h-6 w-6 text-xs',
  sm: 'h-8 w-8 text-sm',
  md: 'h-10 w-10 text-base',
  lg: 'h-14 w-14 text-lg',
  xl: 'h-20 w-20 text-2xl',
};

const statusColors = {
  online: 'bg-green-500',
  offline: 'bg-gray-400',
  busy: 'bg-red-500',
  away: 'bg-yellow-500',
};

const Avatar = React.forwardRef(
  (
    {
      src,
      alt = '',
      name = '',
      size = 'md',
      status,
      animate = 'none',
      animationDelay = 0,
      className = '',
      onClick,
      onError,
      ...props
    },
    ref
  ) => {
    const [error, setError] = useState(false);
    const initials = name
      .split(' ')
      .filter(Boolean)
      .map((n) => n[0])
      .slice(0, 2)
      .join('')
      .toUpperCase();

    const handleError = (e) => {
      setError(true);
      onError?.(e);
    };

    return (
      <div
        ref={ref}
        className={cn(
          'relative inline-flex',
          getAnimationClass(animate, animationDelay),
          className
        )}
        {...props}
      >
        {src && !error ? (
          <img
            src={src}
            alt={alt || name}
            onError={handleError}
            onClick={onClick}
            className={cn(
              sizes[size],
              'rounded-full object-cover border-2 border-border transition-transform duration-200',
              onClick && 'cursor-pointer hover:scale-105'
            )}
          />
        ) : (
          <div
            className={cn(
              sizes[size],
              'rounded-full bg-primary/10 text-primary flex items-center justify-center font-semibold border-2 border-border select-none transition-transform duration-200',
              onClick && 'cursor-pointer hover:scale-105'
            )}
            onClick={onClick}
            role={onClick ? 'button' : undefined}
            tabIndex={onClick ? 0 : undefined}
            aria-label={alt || name || 'Avatar'}
            onKeyDown={
              onClick
                ? (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      onClick(e);
                    }
                  }
                : undefined
            }
          >
            {initials || '?'}
          </div>
        )}
        {status && (
          <span
            className={cn(
              'absolute bottom-0 right-0 block h-2.5 w-2.5 rounded-full ring-2 ring-background',
              statusColors[status]
            )}
            aria-label={`Status: ${status}`}
          />
        )}
      </div>
    );
  }
);

Avatar.displayName = 'Avatar';

export default Avatar;
