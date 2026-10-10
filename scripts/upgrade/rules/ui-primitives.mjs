/**
 * Rule: ui-primitives
 *
 * Adds src/shared/ui — a small primitive layer an app can actually import:
 *
 *  - zero new dependencies (styling rides the app's own --t-* tokens and its
 *    existing .btn-primary/.btn-outline component classes);
 *  - WAI-ARIA correct by construction (aria-busy while loading, aria-disabled,
 *    aria-hidden on decorative icons, keyboard focus ring from the token sheet);
 *  - variant/size/disabled/className props per the house component contract.
 *
 * Files are created once. A file whose marker was removed, i.e. a file someone
 * is editing by hand, is never overwritten.
 */
const MARK = 'LUMI_UI_V8';

const BUTTON = `/**
 * Button — ${MARK}
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
`;

const BADGE = `/**
 * Badge — ${MARK}
 *
 * Status/category label. Tone colours are mixed toward --t-text so small text
 * keeps its contrast ratio against the tinted background instead of failing
 * 4.5:1 the way a raw status hue would.
 */
import React from 'react';
import { cn } from '../../utils.js';

const TONES = {
  neutral: 'bg-[color-mix(in_srgb,var(--t-muted)_12%,transparent)] text-[var(--t-heading)]',
  primary: 'bg-[color-mix(in_srgb,var(--t-primary)_14%,transparent)] text-[var(--t-primary)]',
  success:
    'bg-[color-mix(in_srgb,var(--t-success)_16%,transparent)] text-[color-mix(in_srgb,var(--t-success)_62%,var(--t-text))]',
  warning:
    'bg-[color-mix(in_srgb,var(--t-warn)_18%,transparent)] text-[color-mix(in_srgb,var(--t-warn)_55%,var(--t-text))]',
  danger:
    'bg-[color-mix(in_srgb,var(--t-error)_16%,transparent)] text-[color-mix(in_srgb,var(--t-error)_65%,var(--t-text))]',
};

const Badge = ({ tone = 'neutral', className, children, ...rest }) => (
  <span
    className={cn(
      'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold',
      TONES[tone] ?? TONES.neutral,
      className
    )}
    {...rest}
  >
    {children}
  </span>
);

export default Badge;
`;

const CARD = `/**
 * Card — ${MARK}
 *
 * Surface container. \`as\` keeps the semantics the caller needs (article for a
 * listing, li inside a list) instead of forcing a div, and \`interactive\` only
 * adds the lift when the card really is clickable.
 */
import React from 'react';
import { cn } from '../../utils.js';

const Card = ({ as: Tag = 'div', interactive = false, className, children, ...rest }) => (
  <Tag
    className={cn(
      'rounded-[var(--t-radius-card,var(--t-radius-lg,1rem))] border border-[var(--t-border)]',
      'bg-[var(--t-surface)] p-6 shadow-[var(--t-shadow-md)]',
      'dark:border-[color-mix(in_srgb,var(--t-border)_75%,transparent)]',
      interactive && 'card-lift cursor-pointer',
      className
    )}
    {...rest}
  >
    {children}
  </Tag>
);

export default Card;
`;

const UI_BARREL = `/* ${MARK} — primitive barrel. Import from here, not from the files. */
export { default as Button } from './Button.jsx';
export { default as Badge } from './Badge.jsx';
export { default as Card } from './Card.jsx';
`;

const SHARED_BARREL = `/* ${MARK} — shared UI surface, re-exported so features import one path. */
export { Button, Badge, Card } from './ui/index.js';
`;

const FILES = [
  { path: 'src/shared/ui/Button.jsx', content: BUTTON },
  { path: 'src/shared/ui/Badge.jsx', content: BADGE },
  { path: 'src/shared/ui/Card.jsx', content: CARD },
  { path: 'src/shared/ui/index.js', content: UI_BARREL, barrel: true },
  { path: 'src/shared/index.js', content: SHARED_BARREL, barrel: true },
];

/**
 * A barrel holds nothing but re-export lines, a header comment and blank lines,
 * so it is safe to regenerate. Anything else means a human is using the file and
 * it gets left alone.
 */
function isGeneratedBarrel(content) {
  return content
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .every((line) => line.startsWith('export') || line.startsWith('/*') || line.startsWith('//') || line.startsWith('*'));
}

export default {
  id: 'ui-primitives',
  version: '1.0.1',
  title: 'src/shared/ui primitives (Button/Badge/Card), token-driven + ARIA',
  watch: ['src/shared/ui/Button.jsx'],
  plan(ctx) {
    if (!ctx.has('src/utils.js')) {
      ctx.note('no src/utils.js exporting cn() — primitives need it, skipped');
      return [];
    }

    const ops = [];
    for (const file of FILES) {
      const current = ctx.get(file.path);
      if (current === null) {
        ops.push({ kind: 'create', path: file.path, content: file.content });
        continue;
      }
      if (current.includes(MARK)) continue;
      if (file.barrel && isGeneratedBarrel(current)) {
        ops.push({ kind: 'update', path: file.path, content: file.content });
        continue;
      }
      ctx.note(`${file.path} exists without the marker — left untouched`);
    }
    return ops;
  },
};
