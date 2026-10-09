import React from 'react';
import { BRAND } from './BRAND';

/**
 * The Aurelia Estates mark: a gradient tile carrying a pitched-roof villa with arched doorway.
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
        <polygon points='8,30 32,8 56,30' fill='#ffffff'/><rect x='16' y='30' width='32' height='24' fill='#ffffff'/><path d='M28 54 V44 C28 38 36 38 36 44 V54 Z' fill='#821616'/><circle cx='45' cy='22' r='4' fill='#821616'/>
      </g>
    </svg>
  );
}

export default BrandMark;