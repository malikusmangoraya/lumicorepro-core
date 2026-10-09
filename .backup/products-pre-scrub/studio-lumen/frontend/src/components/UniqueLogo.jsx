import React from 'react';
import { Link } from 'react-router-dom';

export default function UniqueLogo({ size = 'md' }) {
  const sz = { sm: 24, md: 32, lg: 40 }[size] || 32;
  return (
    <Link
      to="/"
      className="inline-flex items-center gap-2.5 select-none transition-opacity hover:opacity-90"
    >
      <div style={{ width: sz, height: sz }} className="shrink-0">
        <svg
          viewBox="0 0 48 48"
          width="100%"
          height="100%"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <polygon
            points="24,4 42,14 42,34 24,44 6,34 6,14"
            fill="var(--t-primary)"
            opacity="0.95"
          />
          <polygon points="24,12 34,18 34,30 24,36 14,30 14,18" fill="white" opacity="0.9" />
          <polygon points="24,18 29,21 29,27 24,30 19,27 19,21" fill="var(--t-accent)" />
        </svg>
      </div>
      <span className="font-extrabold text-xl tracking-tight" style={{ color: 'var(--t-heading)' }}>
        Studio
      </span>
    </Link>
  );
}
