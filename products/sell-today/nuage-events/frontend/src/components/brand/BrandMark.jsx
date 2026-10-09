import React from 'react';
import { BRAND } from './BRAND';

/**
 * The Nuage Events mark: a gradient tile carrying a celebration burst with confetti and spark.
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
        <polygon points='32,6 36,26 58,32 36,38 32,58 28,38 6,32 28,26' fill='#ffffff'/><circle cx='24' cy='42' r='7' fill='#ffffff'/><circle cx='42' cy='44' r='5' fill='#ffffff'/><rect x='12' y='14' width='4' height='4' rx='1' fill='#0ea5e9'/><rect x='48' y='14' width='3' height='3' rx='1' fill='#0ea5e9'/>
      </g>
    </svg>
  );
}

export default BrandMark;