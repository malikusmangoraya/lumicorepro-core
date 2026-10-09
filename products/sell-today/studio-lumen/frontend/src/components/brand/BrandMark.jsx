import React from 'react';
import { BRAND } from './BRAND';

/**
 * The Studio Lumen mark: a gradient tile carrying a dual optic lens with light flare.
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
        <circle cx='32' cy='32' r='22' fill='none' stroke='#ffffff' stroke-width='4'/><circle cx='32' cy='32' r='13' fill='none' stroke='#ffffff' stroke-width='3'/><circle cx='32' cy='32' r='6' fill='#ffffff'/><polygon points='46,14 48,21 55,23 48,25 46,32 44,25 37,23 44,21' fill='#ffffff'/><line x1='32' y1='4' x2='32' y2='8' stroke='#ffffff' stroke-width='2.5' stroke-linecap='round'/>
      </g>
    </svg>
  );
}

export default BrandMark;