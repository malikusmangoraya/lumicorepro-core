import React from 'react';
import { BRAND } from './BRAND';

/**
 * The Aurum Fitness mark: a gradient tile carrying a power barbell with plated ends and energy core.
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
        <rect x='4' y='28' width='56' height='8' rx='4' fill='#ffffff'/><rect x='10' y='16' width='11' height='32' rx='3' fill='#ffffff'/><rect x='43' y='16' width='11' height='32' rx='3' fill='#ffffff'/><polygon points='32,10 26,28 37,28 30,46' fill='#ffffff'/>
      </g>
    </svg>
  );
}

export default BrandMark;