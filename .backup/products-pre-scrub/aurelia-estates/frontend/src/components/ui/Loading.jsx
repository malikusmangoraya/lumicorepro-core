import React from 'react';
import Spinner from './Spinner';
import { cn, getAnimationClass } from '../../utils';

const Loading = ({
  text = 'Loading...',
  fullScreen = false,
  size = 'md',
  animate = 'fade',
  className = '',
  ...props
}) => {
  const content = (
    <>
      <Spinner size={size} />
      {text && <p className="mt-3 text-sm text-muted-foreground">{text}</p>}
    </>
  );

  if (fullScreen) {
    return (
      <div
        className={cn(
          'fixed inset-0 z-50 flex flex-col items-center justify-center bg-background/80 backdrop-blur-sm',
          getAnimationClass(animate)
        )}
        role="status"
        aria-live="polite"
        {...props}
      >
        {content}
      </div>
    );
  }

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-12',
        getAnimationClass(animate),
        className
      )}
      role="status"
      aria-live="polite"
      {...props}
    >
      {content}
    </div>
  );
};

export default Loading;
