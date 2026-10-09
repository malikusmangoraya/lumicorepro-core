import React from 'react';
import { motion } from 'framer-motion';
import { cn, getAnimationClass } from '../../utils';

const StatsCard = React.forwardRef(
  (
    {
      title,
      value,
      change,
      changeLabel,
      icon: Icon,
      iconColor = 'primary',
      trend = 'neutral',
      className = '',
      animate = 'fade-up',
      animationDelay = 0,
      children,
      ...props
    },
    ref
  ) => {
    const trendColors = {
      up: 'text-emerald-600 dark:text-emerald-400',
      down: 'text-red-600 dark:text-red-400',
      neutral: 'text-muted-foreground',
    };

    const trendIcons = {
      up: '↑',
      down: '↓',
      neutral: '→',
    };

    return (
      <motion.div
        ref={ref}
        className={cn(
          'group relative p-6 rounded-2xl bg-card border border-border transition-all duration-300',
          'hover:shadow-lg hover:-translate-y-1 hover:border-primary/20',
          getAnimationClass(animate, animationDelay),
          className
        )}
        whileHover={{ y: -4, boxShadow: '0 20px 40px -12px rgba(0,0,0,0.15)' }}
        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
        {...props}
      >
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className="font-display text-3xl font-bold text-foreground">{value}</p>
            {change !== undefined && (
              <div className="flex items-center gap-1.5">
                <span className={cn('text-sm font-semibold', trendColors[trend])}>
                  {trendIcons[trend]} {Math.abs(change)}%
                </span>
                {changeLabel && (
                  <span className="text-xs text-muted-foreground">{changeLabel}</span>
                )}
              </div>
            )}
          </div>
          {Icon && (
            <div
              className={cn(
                'p-3 rounded-xl shrink-0 transition-all duration-300 group-hover:scale-110',
                `bg-${iconColor}-500/10 text-${iconColor}-500`
              )}
            >
              <Icon className="h-6 w-6" aria-hidden="true" />
            </div>
          )}
        </div>
        {children && <div className="mt-4">{children}</div>}
      </motion.div>
    );
  }
);

StatsCard.displayName = 'StatsCard';

export default StatsCard;