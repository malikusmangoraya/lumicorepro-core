import React from 'react';

export function LogoMark({ size = 28, className = '' }) {
  return (
    <svg viewBox="0 0 48 48" width={size} height={size} className={className} fill="none">
      <defs>
        <linearGradient id="brand-grad-logo" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="rgb(6, 182, 212)" />
          <stop offset="100%" stopColor="rgb(139, 92, 246)" />
        </linearGradient>
      </defs>
      <polygon
        points="24,4 42,14 42,34 24,44 6,34 6,14"
        fill="url(#brand-grad-logo)"
        opacity="0.95"
      />
      <polygon points="24,12 34,18 34,30 24,36 14,30 14,18" fill="white" opacity="0.9" />
      <polygon points="24,18 29,21 29,27 24,30 19,27 19,21" fill="url(#brand-grad-logo)" />
    </svg>
  );
}

export default function BrandLogo({ size = 'md', className = '' }) {
  const sz = { sm: 20, md: 28, lg: 36 }[size] || 28;
  return (
    <svg viewBox="0 0 48 48" width={sz} height={sz} className={className} fill="none">
      <defs>
        <linearGradient id="brand-grad-mini" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="rgb(6, 182, 212)" />
          <stop offset="100%" stopColor="rgb(139, 92, 246)" />
        </linearGradient>
      </defs>
      <polygon
        points="24,4 42,14 42,34 24,44 6,34 6,14"
        fill="url(#brand-grad-mini)"
        opacity="0.95"
      />
      <polygon points="24,12 34,18 34,30 24,36 14,30 14,18" fill="white" opacity="0.9" />
      <polygon points="24,18 29,21 29,27 24,30 19,27 19,21" fill="url(#brand-grad-mini)" />
    </svg>
  );
}
