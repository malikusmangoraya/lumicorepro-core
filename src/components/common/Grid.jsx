import React from 'react';
import { cn, getAnimationClass } from '../../utils';

const colsMap = {
  1: 'grid-cols-1',
  2: 'grid-cols-1 sm:grid-cols-2',
  3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
  4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4',
  5: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-5',
  6: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6',
};

const gaps = {
  none: 'gap-0',
  sm: 'gap-3',
  md: 'gap-6',
  lg: 'gap-8',
  xl: 'gap-10',
};

const Grid = React.forwardRef(
  (
    {
      children,
      cols = 3,
      gap = 'md',
      as: Component = 'div',
      animate = 'none',
      animationDelay = 0,
      className = '',
      ...props
    },
    ref
  ) => (
    <Component
      ref={ref}
      className={cn(
        'grid',
        colsMap[cols] || colsMap[3],
        gaps[gap] || gaps.md,
        getAnimationClass(animate, animationDelay),
        className
      )}
      {...props}
    >
      {children}
    </Component>
  )
);

Grid.displayName = 'Grid';

export default Grid;
