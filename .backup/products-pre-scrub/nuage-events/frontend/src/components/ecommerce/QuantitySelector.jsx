import React from 'react';
import { Minus, Plus } from 'lucide-react';
import { cn } from '../../utils';

const QuantitySelector = ({
  value = 1,
  onChange,
  min = 1,
  max = 99,
  size = 'md',
  className = '',
  label = 'Quantity',
}) => {
  const sizes = { sm: 'h-8 text-xs', md: 'h-10 text-sm', lg: 'h-12 text-base' };
  const btnSizes = { sm: 'h-8 w-8', md: 'h-10 w-10', lg: 'h-12 w-12' };

  const clamp = (next) => Math.min(Math.max(next, min), max);

  const step = (delta) => {
    if (typeof onChange === 'function') onChange(clamp(value + delta));
  };

  return (
    <div className={cn('inline-flex items-center', className)}>
      <label className="sr-only">{label}</label>
      <div className="inline-flex items-center overflow-hidden rounded-lg border bg-background">
        <button
          type="button"
          onClick={() => step(-1)}
          disabled={value <= min}
          aria-label="Decrease quantity"
          className={cn(
            'flex items-center justify-center text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40 disabled:cursor-not-allowed disabled:opacity-40',
            btnSizes[size] || btnSizes.md
          )}
        >
          <Minus className="h-4 w-4" aria-hidden="true" />
        </button>
        <input
          type="number"
          value={value}
          min={min}
          max={max}
          onChange={(e) => {
            const parsed = parseInt(e.target.value, 10);
            if (Number.isFinite(parsed) && typeof onChange === 'function') {
              onChange(clamp(parsed));
            }
          }}
          aria-label={label}
          className={cn(
            'w-12 border-x bg-transparent text-center font-semibold text-foreground outline-none focus:ring-2 focus:ring-inset focus:ring-primary/40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none',
            sizes[size] || sizes.md
          )}
        />
        <button
          type="button"
          onClick={() => step(1)}
          disabled={value >= max}
          aria-label="Increase quantity"
          className={cn(
            'flex items-center justify-center text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40 disabled:cursor-not-allowed disabled:opacity-40',
            btnSizes[size] || btnSizes.md
          )}
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
};

export default QuantitySelector;
