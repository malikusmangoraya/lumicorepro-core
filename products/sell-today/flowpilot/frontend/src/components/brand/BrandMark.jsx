import React from 'react';
import { BRAND } from './BRAND';

/**
 * The FlowPilot mark: a gradient tile carrying an orbital flow with launch chevron and hub.
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
        <circle cx='32' cy='32' r='22' fill='none' stroke='#ffffff' stroke-width='4'/><ellipse cx='32' cy='32' rx='22' ry='9' fill='none' stroke='rgba(255,255,255,0.5)' stroke-width='2.5'/><polygon points='27,18 43,32 27,46 21,46 35,32 21,18' fill='#ffffff'/><circle cx='32' cy='32' r='5' fill='#059669'/><polygon points='48,8 51,11 48,14 45,11' fill='#ffffff'/>
      </g>
    </svg>
  );
}

export default BrandMark;