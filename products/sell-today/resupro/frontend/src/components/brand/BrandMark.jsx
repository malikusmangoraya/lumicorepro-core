import React from 'react';
import { BRAND } from './BRAND';

/**
 * The ResuPro mark: a gradient tile carrying an ascent document with growth arc.
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
        <path d='M20 10 H36 L44 18 V54 H20 Z' fill='#ffffff'/><polygon points='36,10 44,18 36,18' fill='#059669'/><path d='M24 26 H36 M24 33 H32' stroke='#059669' stroke-width='2.5' stroke-linecap='round'/><path d='M24 44 L30 38 L36 40 L42 34' fill='none' stroke='#059669' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'/><polygon points='42,34 37,34 41,30' fill='#059669'/>
      </g>
    </svg>
  );
}

export default BrandMark;