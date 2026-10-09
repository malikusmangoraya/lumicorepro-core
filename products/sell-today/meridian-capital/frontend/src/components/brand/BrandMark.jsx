import React from 'react';
import { BRAND } from './BRAND';

/**
 * The Meridian Capital mark: a gradient tile carrying a meridian globe with rising needle and core.
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
        <circle cx='32' cy='32' r='21' fill='none' stroke='#ffffff' stroke-width='4'/><ellipse cx='32' cy='32' rx='8' ry='21' fill='none' stroke='rgba(255,255,255,0.55)' stroke-width='3'/><line x1='11' y1='32' x2='53' y2='32' stroke='#ffffff' stroke-width='3' stroke-linecap='round'/><polygon points='32,6 35,13 29,13' fill='#ffffff'/><polygon points='32,34 36,34 34,42 30,42' fill='#ffffff'/>
      </g>
    </svg>
  );
}

export default BrandMark;