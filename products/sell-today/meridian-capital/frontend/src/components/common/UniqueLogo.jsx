import React from 'react';

/** UniqueLogo — LUMI_LAYOUT_V1 generated vector mark for Meridian Capital. */
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
    <linearGradient id="grad_140" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#8b5cf6" />
      <stop offset="100%" stop-color="#c084fc" />
    </linearGradient>
  </defs>
  
              <polygon points="24,4 40,14 40,34 24,44 8,34 8,14" fill="none" stroke="url(#grad_140)" stroke-width="3" />
              <circle cx="24" cy="24" r="5" fill="#c084fc" />
              <line x1="24" y1="4" x2="24" y2="19" stroke="url(#grad_140)" stroke-width="2" />
              <line x1="40" y1="34" x2="27" y2="26" stroke="url(#grad_140)" stroke-width="2" />
              <line x1="8" y1="34" x2="21" y2="26" stroke="url(#grad_140)" stroke-width="2" />
            
</svg>` }}
    />
  );
}
