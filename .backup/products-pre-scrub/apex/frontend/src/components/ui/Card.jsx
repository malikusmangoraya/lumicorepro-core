import React from 'react';
import { motion } from 'framer-motion';
import { cn, getAnimationClass } from '../../utils';

const paddings = {
  none: '',
  sm: 'p-3',
  md: 'p-6',
  lg: 'p-8',
};

const shadows = {
  none: '',
  sm: 'shadow-sm',
  md: 'shadow-md',
  lg: 'shadow-lg',
};

const Card = React.forwardRef(
  (
    {
      children,
      className = '',
      hoverable = false,
      padding = 'md',
      bordered = true,
      shadow = 'sm',
      animate = 'none',
      animationDelay = 0,
      as: Component = 'div',
      reveal = false,
      onClick,
      onMouseEnter,
      onMouseLeave,
      ...props
    },
    ref
  ) => {
    const interactive = Boolean(onClick) || hoverable;

    const cardClasses = cn(
      'bg-card text-card-foreground rounded-xl',
      bordered && 'border border-border',
      shadows[shadow],
      paddings[padding],
      interactive &&
        'transition-all duration-200 hover:shadow-md hover:-translate-y-0.5 cursor-pointer',
      getAnimationClass(animate, animationDelay),
      className
    );

    const motionProps =
      interactive && !reveal
        ? {
            whileHover: { y: -4 },
            transition: { type: 'spring', stiffness: 300, damping: 20 },
          }
        : {};

    const content = (
      <Component
        ref={ref}
        className={cardClasses}
        onClick={onClick}
        onMouseEnter={onMouseEnter}
        onMouseLeave={onMouseLeave}
        role={onClick ? 'button' : undefined}
        tabIndex={onClick ? 0 : undefined}
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
        {...motionProps}
        {...props}
      >
        {children}
      </Component>
    );

    if (reveal) {
      return (
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-40px' }}
          transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
          whileHover={{ y: -4 }}
        >
          {content}
        </motion.div>
      );
    }

    return content;
  }
);

Card.displayName = 'Card';

export const CardHeader = React.forwardRef(({ children, className = '', ...props }, ref) => (
  <div ref={ref} className={cn('mb-4', className)} {...props}>
    {children}
  </div>
));
CardHeader.displayName = 'CardHeader';

export const CardTitle = React.forwardRef(
  ({ children, className = '', as: Tag = 'h3', ...props }, ref) => (
    <Tag ref={ref} className={cn('text-lg font-semibold text-foreground', className)} {...props}>
      {children}
    </Tag>
  )
);
CardTitle.displayName = 'CardTitle';

export const CardDescription = React.forwardRef(({ children, className = '', ...props }, ref) => (
  <p ref={ref} className={cn('text-sm text-muted-foreground mt-1', className)} {...props}>
    {children}
  </p>
));
CardDescription.displayName = 'CardDescription';

export const CardContent = React.forwardRef(({ children, className = '', ...props }, ref) => (
  <div ref={ref} className={cn(className)} {...props}>
    {children}
  </div>
));
CardContent.displayName = 'CardContent';

export const CardFooter = React.forwardRef(({ children, className = '', ...props }, ref) => (
  <div ref={ref} className={cn('mt-4 flex items-center', className)} {...props}>
    {children}
  </div>
));
CardFooter.displayName = 'CardFooter';

export default Card;
