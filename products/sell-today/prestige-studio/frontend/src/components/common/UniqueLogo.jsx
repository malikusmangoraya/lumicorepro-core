import React from 'react';

/** UniqueLogo — LUMI_LAYOUT_V1 generated vector mark for Prestige Studio. */
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
    <linearGradient id="grad_1229" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#8b5cf6" />
      <stop offset="100%" stop-color="#c084fc" />
    </linearGradient>
  </defs>
  
              <polygon points="24,6 42,38 6,38" fill="none" stroke="url(#grad_1229)" stroke-width="3" />
              <polygon points="24,18 34,35 14,35" fill="#c084fc" opacity="0.4" />
            
</svg>` }}
    />
  );
}
