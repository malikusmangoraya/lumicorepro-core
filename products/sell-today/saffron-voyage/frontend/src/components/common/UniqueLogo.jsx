import React from 'react';

/** UniqueLogo — LUMI_LAYOUT_V1 generated vector mark for Saffron Voyage. */
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
    <linearGradient id="grad_3371" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#10b981" />
      <stop offset="100%" stop-color="#34d399" />
    </linearGradient>
  </defs>
  
              <polygon points="24,6 42,16 24,26 6,16" fill="url(#grad_3371)" opacity="0.9" />
              <polygon points="6,16 24,26 24,42 6,32" fill="#10b981" opacity="0.75" />
              <polygon points="24,26 42,16 42,32 24,42" fill="#34d399" opacity="0.6" />
            
</svg>` }}
    />
  );
}
