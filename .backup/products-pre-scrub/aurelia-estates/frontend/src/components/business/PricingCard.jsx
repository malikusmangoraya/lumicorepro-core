import ButtonMotion from '@/components/ui/ButtonMotion';
import React from 'react';
import { Check } from 'lucide-react';
import { cn } from '../../utils';

const PricingCard = ({
  name = '',
  price = '',
  period = '',
  description = '',
  features = [],
  highlighted = false,
  animationDelay = 0,
  onSelect,
  className = '',
  ...props
}) => {
  const handleSelect = (e) => {
    const data = { name, price, period, description, features, highlighted };
    onSelect?.(data, e);
  };

  return (
    <div
      className={cn(
        'group relative flex h-full flex-col rounded-2xl border bg-card p-6',
        'transition-all duration-200 hover:-translate-y-1',
        highlighted
          ? 'border-primary/50 bg-primary/5 shadow-glow-sm'
          : 'border-border hover:border-primary/30',
        className
      )}
      style={{ transitionDelay: `${animationDelay}ms` }}
      {...props}
    >
      {highlighted && (
        <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-primary px-3 py-1 text-xs font-semibold text-primary-foreground">
          Popular
        </span>
      )}
      <h3 className="font-display text-lg font-bold text-foreground">{name}</h3>
      {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
      <div className="mt-4 flex items-baseline gap-1">
        <span className="font-display text-3xl font-extrabold text-foreground">{price}</span>
        {period && <span className="text-sm text-muted-foreground">{period}</span>}
      </div>
      <ul className="mt-5 flex-1 space-y-2">
        {features.map((feature, index) => (
          <li key={index} className="flex items-start gap-2 text-sm text-muted-foreground">
            <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
            <span>{feature}</span>
          </li>
        ))}
      </ul>
      <ButtonMotion
        type="button"
        onClick={handleSelect}
        aria-label={`Choose ${name} plan`}
        className={cn(
          'mt-6 w-full rounded-xl px-4 py-2.5 text-sm font-semibold transition-all duration-200',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50',
          highlighted
            ? 'bg-primary text-primary-foreground hover:bg-primary/90'
            : 'border border-border bg-background text-foreground hover:border-primary/40 hover:bg-primary/5'
        )}
      >
        {highlighted ? 'Choose plan' : 'Get started'}
      </ButtonMotion>
    </div>
  );
};

export default PricingCard;
