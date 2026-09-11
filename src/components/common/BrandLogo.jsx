import React from 'react';
import { Link } from 'react-router-dom';
import { cn } from '@/utils';

/* ── Hex mark — pure SVG + CSS animation, zero runtime deps ── */
export function LogoMark({ className = '', size = 32, animated = false }) {
  return (
    <svg
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      className={cn('shrink-0', animated && 'animate-scale-in', className)}
      aria-hidden="true"
    >
      {/* Outer hex */}
      <polygon
        points="24,3 41,12.5 41,31.5 24,41 7,31.5 7,12.5"
        className="fill-primary drop-shadow-sm"
      />
      {/* Middle hex */}
      <polygon
        points="24,11 35,17 35,29 24,35 13,29 13,17"
        fill="currentColor"
        className="text-primary-foreground"
        opacity="0.95"
      />
      {/* Inner diamond */}
      <polygon
        points="24,18.5 29.5,21.5 29.5,26.5 24,29.5 18.5,26.5 18.5,21.5"
        className="fill-primary"
      />
    </svg>
  );
}

/* ── Full wordmark component ─────────────────────────────── */
const BrandLogo = React.forwardRef(
  (
    {
      variant = 'full', // 'full' | 'mark' | 'white'
      size = 'md', // 'sm' | 'md' | 'lg' | 'xl'
      href = '/',
      asLink = true,
      animated = false,
      className = '',
      onClick,
    },
    ref
  ) => {
    const sz = { sm: 22, md: 28, lg: 34, xl: 42 }[size] || 28;
    const textSz =
      { sm: 'text-base', md: 'text-lg', lg: 'text-xl', xl: 'text-2xl' }[size] || 'text-lg';
    const isWhite = variant === 'white';

    const Content = () => (
      <span ref={ref} className={cn('inline-flex items-center gap-2.5 select-none', className)}>
        <LogoMark size={sz} animated={animated} />
        {variant !== 'mark' && (
          <span
            className={cn(
              'font-display font-extrabold tracking-tight leading-none',
              textSz,
              isWhite ? 'text-white' : 'text-foreground'
            )}
          >
            Lumicore
            <span className={isWhite ? 'text-teal-300' : 'text-primary'}>Pro</span>
          </span>
        )}
      </span>
    );

    if (!asLink) {
      return (
        <span className="inline-flex items-center" onClick={onClick}>
          <Content />
        </span>
      );
    }

    return (
      <Link
        to={href}
        onClick={onClick}
        className="inline-flex items-center transition-opacity hover:opacity-85 active:scale-[0.98]"
        aria-label="LumicorePro home"
      >
        <Content />
      </Link>
    );
  }
);

BrandLogo.displayName = 'BrandLogo';
export default BrandLogo;
