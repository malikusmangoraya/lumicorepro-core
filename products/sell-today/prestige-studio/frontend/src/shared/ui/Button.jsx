/**
 * Button — LUMI_UI_V8
 *
 * Variants and sizes are pure token/CSS-class mappings, so the primitive adopts
 * whatever brand palette the app declares. Loading and disabled are separate
 * concerns: a loading button is also disabled, and says so to assistive tech.
 */
import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '../../utils.js';

const VARIANTS = {
  primary: 'btn-primary',
  outline: 'btn-outline',
  ghost:
    'bg-transparent text-[var(--t-heading)] hover:bg-[color-mix(in_srgb,var(--t-primary)_10%,transparent)]',
  danger: 'bg-[var(--t-error)] text-white hover:opacity-90',
};

const SIZES = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-5 py-2.5 text-sm',
  lg: 'px-7 py-3.5 text-base',
};

const Button = React.forwardRef(function Button(
  {
    variant = 'primary',
    size = 'md',
    loading = false,
    disabled = false,
    icon: Icon,
    type = 'button',
    className,
    children,
    ...rest
  },
  ref
) {
  const isDisabled = disabled || loading;
  const Variant = VARIANTS[variant] ?? VARIANTS.primary;
  const Size = SIZES[size] ?? SIZES.md;

  return (
    <button
      ref={ref}
      type={type}
      disabled={isDisabled}
      aria-busy={loading || undefined}
      className={cn(
        'inline-flex items-center justify-center gap-2 font-semibold transition-all duration-200',
        'rounded-[var(--t-radius-md,0.5rem)] disabled:cursor-not-allowed disabled:opacity-60',
        Variant,
        Size,
        className
      )}
      {...rest}
    >
      {loading ? (
        <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
      ) : Icon ? (
        <Icon className="h-4 w-4" aria-hidden="true" />
      ) : null}
      {children}
    </button>
  );
});

export default Button;
