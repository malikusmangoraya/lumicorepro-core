import React from 'react';
import { cn } from '../../utils';
import Avatar from './Avatar';

const AvatarGroup = React.forwardRef(
  (
    {
      avatars = [],
      maxVisible = 5,
      size = 'md',
      className = '',
      onClick,
      ...props
    },
    ref
  ) => {
    const sizes = {
      xs: 'h-6 w-6 text-xs',
      sm: 'h-7 w-7 text-xs',
      md: 'h-8 w-8 text-sm',
      lg: 'h-10 w-10 text-base',
      xl: 'h-12 w-12 text-lg',
    };

    const spacing = {
      xs: '-space-x-1',
      sm: '-space-x-1.5',
      md: '-space-x-2',
      lg: '-space-x-2.5',
      xl: '-space-x-3',
    };

    const visibleAvatars = avatars.slice(0, maxVisible);
    const remainingCount = avatars.length - maxVisible;

    return (
      <div
        ref={ref}
        className={cn(
          'inline-flex',
          spacing[size],
          className
        )}
        role="group"
        aria-label={`${avatars.length} users`}
        {...props}
      >
        {visibleAvatars.map((avatar, index) => (
          <Avatar
            key={avatar.id || index}
            src={avatar.src}
            alt={avatar.name || avatar.alt}
            name={avatar.name}
            size={size}
            className={cn(
              'border-2 border-background ring-2 ring-background',
              'transition-all duration-200 hover:z-10 hover:ring-primary/50 hover:scale-110'
            )}
            onClick={() => onClick?.(avatar, index)}
          />
        ))}
        {remainingCount > 0 && (
          <div
            className={cn(
              'inline-flex items-center justify-center rounded-full border-2 border-background ring-2 ring-background bg-muted',
              'font-medium text-muted-foreground',
              sizes[size]
            )}
            aria-label={`${remainingCount} more users`}
          >
            +{remainingCount}
          </div>
        )}
      </div>
    );
  }
);

AvatarGroup.displayName = 'AvatarGroup';

export default AvatarGroup;