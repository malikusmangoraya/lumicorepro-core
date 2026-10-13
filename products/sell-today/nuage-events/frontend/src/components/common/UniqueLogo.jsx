import React from 'react';

/** UniqueLogo — LUMI_LAYOUT_V1 generated vector mark for Nuage Events. */
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
    <linearGradient id="grad_4857" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0284c7" />
      <stop offset="100%" stop-color="#38bdf8" />
    </linearGradient>
  </defs>
  
              <ellipse cx="24" cy="24" rx="18" ry="8" transform="rotate(-30 24 24)" fill="none" stroke="url(#grad_4857)" stroke-width="2.5" />
              <ellipse cx="24" cy="24" rx="18" ry="8" transform="rotate(30 24 24)" fill="none" stroke="#38bdf8" stroke-width="2" opacity="0.8" />
              <circle cx="24" cy="24" r="4" fill="url(#grad_4857)" />
            
</svg>` }}
    />
  );
}
