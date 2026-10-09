import React from 'react';
import { BRAND } from './BRAND';

/**
 * The Prestige Studio mark: a gradient tile carrying a precision aperture with framed gem.
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
        <circle cx='32' cy='32' r='22' fill='none' stroke='#ffffff' stroke-width='4'/><polygon points='32,14 47,32 32,50 17,32' fill='none' stroke='#ffffff' stroke-width='2.5'/><circle cx='32' cy='32' r='8' fill='none' stroke='#ffffff' stroke-width='2.5'/><polygon points='32,14 47,32 32,32' fill='rgba(255,255,255,0.5)'/><line x1='32' y1='6' x2='32' y2='10' stroke='#ffffff' stroke-width='3' stroke-linecap='round'/>
      </g>
    </svg>
  );
}

export default BrandMark;