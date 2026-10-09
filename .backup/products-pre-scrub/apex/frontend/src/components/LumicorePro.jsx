import React from 'react';
import { Link } from 'react-router-dom';

export default function BrandLockup({ to = '/', size = 34, dark = false }) {
  const uid = React.useId().replace(/[^a-zA-Z0-9]/g, '');
  const g1 = `br1-${uid}`;
  const g2 = `br2-${uid}`;
  const m1 = `url(#${g1})`;
  const m2 = `url(#${g2})`;
  return (
    <Link
      to={to}
      className="inline-flex items-center gap-2.5 select-none transition-opacity hover:opacity-90"
      aria-label="Apex Digital"
    >
      <svg viewBox="0 0 64 64" width={size} height={size} aria-hidden="true">
        <defs>
          <linearGradient id={g1} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#7c3aed"/>
            <stop offset="1" stop-color="#ec4899"/>
          </linearGradient>
          <linearGradient id={g2} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#ec4899"/>
            <stop offset="1" stop-color="#7c3aed"/>
          </linearGradient>
        </defs>
        <rect x="5" y="5" width="54" height="54" rx="15" fill={m1} opacity="0.14"/>
        <path d="M16 24 A16 16 0 1 1 32 48 A16 16 0 1 1 16 24" fill={m1}/>
        <path d="M16 24 A16 16 0 1 1 32 48 A16 16 0 1 1 16 24" fill="none" stroke={m2} strokeWidth="2.5" strokeLinejoin="round" opacity="0.85"/>
        <text x="32" y="39" text-anchor="middle" font-family="Inter, system-ui, sans-serif"
              font-size="20" font-weight="800" fill="#fff" letter-spacing="0.5">AD</text>
      </svg>
      <span className="font-display font-bold tracking-tight leading-none">
        <span className={dark ? 'text-white' : 'text-slate-900'}>Apex Digital</span>
        <span className="bg-gradient-to-r from-primary to-accent-400 bg-clip-text text-transparent">
          Digital
        </span>
      </span>
    </Link>
  );
}
