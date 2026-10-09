import ButtonMotion from '@/components/ui/ButtonMotion';
import React from 'react';
import { ShoppingBag, ArrowRight } from 'lucide-react';
import { cn } from '../../utils';

const CartEmpty = ({
  title = 'Your cart is empty',
  subtitle = 'Looks like you haven\u2019t added anything yet.',
  onBrowse,
  browseLabel = 'Browse products',
  className = '',
}) => {
  return (
    <div
      className={cn(
        'flex w-full max-w-md flex-col items-center gap-4 py-12 text-center',
        className
      )}
    >
      <div className="flex h-20 w-20 items-center justify-center rounded-full bg-muted">
        <ShoppingBag className="h-9 w-9 text-muted-foreground" aria-hidden="true" />
      </div>
      <div className="space-y-1">
        <h2 className="text-xl font-bold tracking-tight text-foreground">{title}</h2>
        <p className="text-sm text-muted-foreground">{subtitle}</p>
      </div>
      {typeof onBrowse === 'function' && (
        <ButtonMotion
          type="button"
          onClick={onBrowse}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition-all duration-200 hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/40"
        >
          {browseLabel}
          <ArrowRight className="h-4 w-4" aria-hidden="true" />
        </ButtonMotion>
      )}
    </div>
  );
};

export default CartEmpty;
