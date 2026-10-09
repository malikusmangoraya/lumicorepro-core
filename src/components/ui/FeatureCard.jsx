import React from 'react';
import { motion } from 'framer-motion';
import { cn, getAnimationClass } from '../../utils';

const FeatureCard = React.forwardRef(
  (
    {
      title,
      description,
      icon: Icon,
      iconColor = 'primary',
      iconSize = 'md',
      variant = 'default',
      href,
      onClick,
      className = '',
      animate = 'fade-up',
      animationDelay = 0,
      children,
      badge,
      ...props
    },
    ref
  ) => {
    const iconSizes = {
      sm: 'h-5 w-5 p-2.5 rounded-xl',
      md: 'h-6 w-6 p-3 rounded-xl',
      lg: 'h-8 w-8 p-4 rounded-2xl',
      xl: 'h-10 w-10 p-5 rounded-2xl',
    };

    const variants = {
      default: 'bg-card border border-border hover:border-primary/30',
      elevated: 'bg-card shadow-lg hover:shadow-xl border-none',
      glass: 'bg-white/10 dark:bg-slate-900/50 backdrop-blur-xl border border-white/20 dark:border-slate-700/50',
      gradient: 'bg-gradient-to-br from-primary/5 via-transparent to-transparent border border-primary/20',
      outline: 'bg-transparent border-2 border-border hover:border-primary/50',
    };

    const Content = href ? 'a' : onClick ? 'button' : 'div';

    return (
      <motion.div
        ref={ref}
        className={cn(
          'group relative p-6 rounded-2xl transition-all duration-300',
          'hover:-translate-y-1',
          variants[variant],
          getAnimationClass(animate, animationDelay),
          className
        )}
        whileHover={{ y: -4 }}
        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
        {...props}
      >
        {badge && (
          <motion.span
            className="inline-flex items-center gap-1.5 rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-semibold text-primary mb-3"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            {badge}
          </motion.span>
        )}
        {Icon && (
          <motion.div
            className={cn(
              'mb-4 inline-flex items-center justify-center shrink-0 transition-all duration-300 group-hover:scale-110 group-hover:rotate-3',
              `text-${iconColor}-500 bg-${iconColor}-500/10`,
              iconSizes[iconSize]
            )}
            whileHover={{ scale: 1.1, rotate: 3 }}
            aria-hidden="true"
          >
            <Icon className="h-full w-full" />
          </motion.div>
        )}
        <h3 className="font-display text-lg font-bold text-foreground mb-2">{title}</h3>
        {description && (
          <p className="text-sm text-muted-foreground leading-relaxed mb-4">{description}</p>
        )}
        {children && <div className="mt-4">{children}</div>}
        {(href || onClick) && (
          <motion.div
            className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-primary group-hover:gap-3 transition-all duration-200"
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            <span>Learn more</span>
            <motion.span
              className="h-4 w-4"
              animate={{ x: [0, 4, 0] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              →
            </motion.span>
          </motion.div>
        )}
      </motion.div>
    );
  }
);

FeatureCard.displayName = 'FeatureCard';

export default FeatureCard;