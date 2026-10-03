/**
 * BrandLogo — the single canonical logo for the app (mark + lockup).
 *
 * Replaces both `UniqueLogo` (deleted) and the previous mark-only BrandLogo:
 *   <BrandLogo variant="mark" />    geometric prism mark, no text
 *   <BrandLogo variant="lockup" />  mark + gradient wordmark, links home
 *   <BrandLogo variant="full" />    legacy alias of "lockup"
 *
 * Gradient ids come from React `useId()` (sanitised — React ids contain colons,
 * which are unsafe inside `url(#…)`), so several logos can render on one page
 * without one instance stealing another's gradient.
 *
 * Colours are theme tokens (`--primary` / `--accent-foreground`), not hex, so the
 * mark follows light/dark mode and theming.
 */
import { useId } from 'react';
import { Link } from 'react-router-dom';
import { cn } from '../../utils';

export const LOGO_SIZES = { sm: 22, md: 30, lg: 40, xl: 52 };
export const LOGO_WORDMARK_SIZES = {
  sm: 'text-base',
  md: 'text-xl',
  lg: 'text-2xl',
  xl: 'text-3xl',
};
export const DEFAULT_BRAND_NAME = 'LumicorePro';

const GRADIENT_FROM = 'hsl(var(--primary))';
const GRADIENT_TO = 'hsl(var(--accent-foreground))';

const resolveSize = (size) => (typeof size === 'number' ? size : LOGO_SIZES[size] || LOGO_SIZES.md);
const resolveVariant = (variant) => (variant === 'full' ? 'lockup' : variant || 'mark');

function Rays({ glowId }) {
  const offsets = [8, 5, 2, -1, -4];
  return (
    <g stroke={`url(#${glowId})`} strokeWidth="1.6" strokeLinecap="round" opacity="0.85">
      {offsets.map((d) => (
        <line key={`t${d}`} x1="24" y1="4.5" x2="24" y2={String(14 + d)} />
      ))}
      {offsets.map((d) => (
        <line key={`l${d}`} x1="4.5" y1="24" x2={String(14 + d)} y2="24" />
      ))}
      {offsets.map((d) => (
        <line key={`b${d}`} x1="24" y1="43.5" x2="24" y2={String(34 - d)} />
      ))}
    </g>
  );
}

function Prism({ gradId, glowId }) {
  return (
    <g>
      <path
        d="M24 3 L43 14 L43 34 L24 45 L5 34 L5 14 Z"
        fill={`url(#${gradId})`}
        opacity="0.22"
      />
      <path
        d="M24 3 L43 14 L43 34 L24 45 L5 34 L5 14 Z"
        fill="none"
        stroke={GRADIENT_FROM}
        strokeWidth="2"
        opacity="0.95"
      />
      <path
        d="M24 13 L36 19.8 L36 28.2 L24 35 L12 28.2 L12 19.8 Z"
        fill="none"
        stroke="currentColor"
        strokeOpacity="0.9"
        strokeWidth="1.4"
      />
      <circle cx="24" cy="24" r="6.4" fill={`url(#${glowId})`} />
      <path
        d="M20.8 24 h6.4 M24 20.8 v6.4"
        stroke={GRADIENT_TO}
        strokeWidth="1.1"
        strokeLinecap="round"
        opacity="0.8"
      />
    </g>
  );
}

/**
 * The geometric mark on its own.
 * @param {{size?: number|string, className?: string, title?: string}} props
 */
export function LogoMark({ size = LOGO_SIZES.md, className = '', title }) {
  const rawId = useId();
  const uid = rawId.replace(/[^a-zA-Z0-9_-]/g, '');
  const gradId = `${uid}-brand-grad`;
  const glowId = `${uid}-brand-glow`;
  const px = resolveSize(size);

  return (
    <svg
      viewBox="0 0 48 48"
      width={px}
      height={px}
      className={cn('shrink-0', className)}
      fill="none"
      role={title ? 'img' : undefined}
      aria-label={title}
      aria-hidden={title ? undefined : true}
    >
      <defs>
        <linearGradient id={gradId} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor={GRADIENT_FROM} />
          <stop offset="100%" stopColor={GRADIENT_TO} />
        </linearGradient>
        <radialGradient id={glowId} cx="50%" cy="42%" r="55%">
          <stop offset="0%" stopColor="hsl(var(--primary-foreground))" />
          <stop offset="55%" stopColor={GRADIENT_FROM} />
          <stop offset="100%" stopColor={GRADIENT_TO} />
        </radialGradient>
      </defs>
      <Rays glowId={glowId} />
      <Prism gradId={gradId} glowId={glowId} />
    </svg>
  );
}

/**
 * @param {object} props
 * @param {'mark'|'lockup'|'full'} [props.variant='mark']
 * @param {string} [props.name]      — brand name, split into word + accent word
 * @param {'sm'|'md'|'lg'|'xl'|number} [props.size='md']
 * @param {string|null} [props.to='/'] — wrap in a router Link (null renders a plain span)
 */
export default function BrandLogo({
  variant = 'mark',
  name = DEFAULT_BRAND_NAME,
  size = 'md',
  to = '/',
  className = '',
  markClassName = '',
  onClick,
}) {
  const resolved = resolveVariant(variant);
  const px = resolveSize(size);
  const words = String(name)
    .split(/(?=[A-Z])|\s+/)
    .filter(Boolean);
  const primaryWord = words[0] || String(name);
  const accentWord = words.slice(1).join('');

  const mark = <LogoMark size={px} className={markClassName} />;

  if (resolved !== 'lockup') {
    return <span className={cn('inline-flex items-center', className)}>{mark}</span>;
  }

  const content = (
    <>
      {mark}
      <span
        className={cn(
          'font-display font-extrabold tracking-tight text-foreground',
          LOGO_WORDMARK_SIZES[size] || LOGO_WORDMARK_SIZES.md
        )}
      >
        {primaryWord}
        {accentWord && (
          <span className="ml-0.5 bg-gradient-to-r from-primary to-accent-foreground bg-clip-text text-transparent">
            {accentWord}
          </span>
        )}
      </span>
    </>
  );

  const classes = cn(
    'inline-flex select-none items-center gap-2.5 transition-opacity hover:opacity-90',
    className
  );

  if (!to) {
    return (
      <span className={classes}>
        {content}
      </span>
    );
  }

  return (
    <Link to={to} onClick={onClick} className={classes} aria-label={`${name} home`}>
      {content}
    </Link>
  );
}
