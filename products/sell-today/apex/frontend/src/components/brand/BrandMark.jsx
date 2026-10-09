import React from 'react';
import { BRAND } from './BRAND';

/**
 * The Apex Digital mark: a gradient tile carrying a two-tone summit peak with ridge and orb.
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
        <polygon points='8,50 32,6 56,50' fill='none' stroke='#ffffff' stroke-width='5.5' stroke-linejoin='round'/><polygon points='32,6 56,50 32,50' fill='rgba(255,255,255,0.92)'/><polygon points='32,6 44,50 32,50' fill='rgba(255,255,255,0.55)'/><line x1='32' y1='6' x2='32' y2='50' stroke='#ffffff' stroke-width='4' stroke-linecap='round'/><circle cx='32' cy='24' r='5' fill='#ffffff'/>
      </g>
    </svg>
  );
}

export default BrandMark;