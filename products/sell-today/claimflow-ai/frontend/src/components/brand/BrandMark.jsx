import React from 'react';
import { BRAND } from './BRAND';

/**
 * The ClaimFlow mark: a gradient tile carrying a resolved shield with flowing check and crown notch.
 * Vector only - no raster assets - so it stays crisp at any size and
 * inherits the surrounding layout.
 */
export function BrandMark({ size = 34, className = '', title, ...rest }) {
  const uid = React.useId().replace(/[^a-zA-Z0-9]/g, '');
  const gid = `bm-${uid}`;
  const label = title || BRAND.name;
  return (
    <svg
      viewBox="0 0 64 64"
      width={size}
      height={size}
      className={className}
      role="img"
      aria-label={label}
      {...rest}
    >
      <defs>
        <linearGradient id={gid} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor={BRAND.primary} />
          <stop offset="100%" stopColor={BRAND.secondary} />
        </linearGradient>
      </defs>
      <rect width="64" height="64" rx="14.3" fill={`url(#${gid})`} />
      <g transform="translate(14.0 14.0) scale(0.5625)">
        <path d='M32 8 L52 16 V30 C52 42 43 50 32 54 C21 50 12 42 12 30 V16 Z' fill='#ffffff'/><path d='M25 31 L30 37 L41 24' fill='none' stroke='#dc2626' stroke-width='4.5' stroke-linecap='round' stroke-linejoin='round'/><path d='M32 8 L52 16 L32 20 L12 16 Z' fill='rgba(255,255,255,0.55)'/>
      </g>
    </svg>
  );
}

export default BrandMark;