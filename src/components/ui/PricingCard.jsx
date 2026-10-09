import React from 'react';
import { motion } from 'framer-motion';
import { cn, getAnimationClass } from '../../utils';
import { Check } from 'lucide-react';
import Button from './Button';

const PricingCard = React.forwardRef(
  (
    {
      name,
      price,
      period = '/month',
      description,
      features = [],
      ctaText = 'Get Started',
      ctaVariant = 'primary',
      onCtaClick,
      href,
      highlighted = false,
      badge,
      className = '',
      animate = 'fade-up',
      animationDelay = 0,
      ...props
    },
    ref
  ) => {
    const variants = {
      default: 'bg-card border border-border',
      highlighted: 'bg-card border-2 border-primary shadow-lg shadow-primary/10',
      glass: 'bg-white/10 dark:bg-slate-900/50 backdrop-blur-xl border border-white/20 dark:border-slate-700/50',
    };

    const Content = href ? 'a' : 'div';

    return (
      <motion.div
        ref={ref}
        className={cn(
          'relative p-6 rounded-2xl transition-all duration-300 flex flex-col',
          variants[highlighted ? 'highlighted' : 'default'],
          getAnimationClass(animate, animationDelay),
          className
        )}
        whileHover={{ y: -8, boxShadow: '0 25px 50px -12px rgba(0,0,0,0.15)' }}
        transition={{ type: 'spring', stiffness: 250, damping: 20 }}
        {...props}
      >
        {badge && (
          <motion.div
            className="absolute -top-3 left-1/2 -translate-x-1/2"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <span className="inline-flex items-center gap-1.5 rounded-full bg-primary px-3 py-1 text-xs font-bold text-primary-foreground">
              {badge}
            </span>
          </motion.div>
        )}
        {highlighted && (
          <motion.div
            className="absolute top-0 left-1/2 -translate-x-1/2 h-1 w-3/4 bg-gradient-to-r from-primary to-cyan-400 rounded-b-full"
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ delay: 0.1, duration: 0.5 }}
          />
        )}
        <div className="space-y-4 mb-6">
          <h3 className="font-display text-xl font-bold text-foreground">{name}</h3>
          <div className="flex items-baseline gap-1">
            <span className="font-display text-4xl font-bold text-foreground">{price}</span>
            <span className="text-muted-foreground">{period}</span>
          </div>
          {description && <p className="text-sm text-muted-foreground">{description}</p>}
        </div>
        <ul className="space-y-3 mb-6 flex-1" role="list">
          {features.map((feature, i) => (
            <motion.li
              key={i}
              className="flex items-start gap-3 text-sm text-muted-foreground"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 + i * 0.05 }}
            >
              <Check className="h-5 w-5 text-emerald-500 shrink-0 mt-0.5" aria-hidden="true" />
              <span>{feature}</span>
            </motion.li>
          ))}
        </ul>
        <Button
          variant={ctaVariant}
          size="lg"
          fullWidth
          onClick={onCtaClick}
          as={href ? 'a' : 'button'}
          href={href}
          className="mt-auto"
        >
          {ctaText}
        </Button>
      </motion.div>
    );
  }
);

PricingCard.displayName = 'PricingCard';

export default PricingCard;