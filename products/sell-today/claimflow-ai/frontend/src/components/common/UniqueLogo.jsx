import React from 'react';

/** UniqueLogo — LUMI_LAYOUT_V1 generated vector mark for Claimflow Ai 002. */
export default function UniqueLogo({ size = 40, className = '', label = '' }) {
  return (
    <span
      className={className}
      role={label ? 'img' : undefined}
      aria-label={label || undefined}
      aria-hidden={label ? undefined : true}
      style={{ display: 'inline-flex', width: size, height: size }}
      dangerouslySetInnerHTML={{ __html: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" class="w-10 h-10 inline-block">
  <defs>
    <linearGradient id="grad_1008" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#10b981" />
      <stop offset="100%" stop-color="#34d399" />
    </linearGradient>
  </defs>
  
              <path d="M14 18 C 8 18, 8 30, 14 30 C 20 30, 28 18, 34 18 C 40 18, 40 30, 34 30 C 28 30, 20 18, 14 18 Z" fill="none" stroke="url(#grad_1008)" stroke-width="3" stroke-linecap="round" />
            
</svg>` }}
    />
  );
}
