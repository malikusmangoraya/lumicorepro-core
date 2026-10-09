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
          <rect x="4" y="4" width="40" height="40" rx="12" fill="var(--t-primary)" opacity="0.95" />
          <rect x="12" y="12" width="24" height="24" rx="6" fill="white" opacity="0.9" />
          <rect x="18" y="18" width="12" height="12" rx="3" fill="var(--t-accent)" />
        </svg>
      </div>
      <span className="font-extrabold text-xl tracking-tight" style={{ color: 'var(--t-heading)' }}>
        Prestige
      </span>
    </Link>
  );
}
