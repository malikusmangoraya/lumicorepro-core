import React from 'react';
import { BRAND } from './BRAND';

/**
 * The Saffron Voyage mark: a gradient tile carrying a cardinal compass with south needle and pivot.
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
        <circle cx='32' cy='32' r='22' fill='none' stroke='#ffffff' stroke-width='4'/><polygon points='32,12 39,32 32,52 25,32' fill='#ffffff'/><polygon points='32,22 36,32 32,52 28,32' fill='#0ea5e9'/><circle cx='32' cy='32' r='4' fill='#ffffff'/><polygon points='6,22 9,14 12,22 9,26' fill='#ffffff'/>
      </g>
    </svg>
  );
}

export default BrandMark;