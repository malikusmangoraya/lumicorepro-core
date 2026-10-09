import React from 'react';
import { TrendingUp, TrendingDown, DollarSign } from 'lucide-react';
import { cn } from '../../utils';

const RevenueCard = ({
  label = 'Revenue',
  value = 0,
  change = 0,
  currency = 'USD',
  icon: Icon = DollarSign,
  mode = 'value',
  className = '',
}) => {
  const formatCurrency = (n) => {
    try {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency,
        notation: mode === 'compact' ? 'compact' : 'standard',
      }).format(n);
    } catch (e) {
      return n;
    }
  };

  const positive = change >= 0;

  return (
    <article
      className={cn('rounded-2xl border bg-card p-5 text-card-foreground shadow-sm', className)}
    >
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-muted-foreground">{label}</p>
        <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Icon className="h-4 w-4" aria-hidden="true" />
        </span>
      </div>
      <p className="mt-3 text-2xl font-bold tabular-nums text-foreground">
        {formatCurrency(value)}
      </p>
      <div className="mt-2 flex items-center gap-2">
        <span
          className={cn(
            'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold',
            positive
              ? 'bg-green-600/10 text-green-700 dark:text-green-400'
              : 'bg-destructive/10 text-destructive'
          )}
        >
          {positive ? (
            <TrendingUp className="h-3 w-3" aria-hidden="true" />
          ) : (
            <TrendingDown className="h-3 w-3" aria-hidden="true" />
          )}
          {positive ? '+' : ''}
          {change}%
        </span>
        <span className="text-xs text-muted-foreground">vs last month</span>
      </div>
    </article>
  );
};

export default RevenueCard;
