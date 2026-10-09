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
          <rect
            x="8"
            y="8"
            width="32"
            height="32"
            rx="4"
            fill="var(--t-primary)"
            transform="rotate(45 24 24)"
            opacity="0.95"
          />
          <circle cx="24" cy="24" r="10" fill="white" opacity="0.9" />
          <circle cx="24" cy="24" r="6" fill="var(--t-accent)" />
        </svg>
      </div>
      <span className="font-extrabold text-xl tracking-tight" style={{ color: 'var(--t-heading)' }}>
        Meridian
      </span>
    </Link>
  );
}
