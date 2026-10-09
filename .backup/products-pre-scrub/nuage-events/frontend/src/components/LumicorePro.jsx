import React from 'react';
import { Link } from 'react-router-dom';

export default function LumicorePro({ to = '/', size = 34, dark = false }) {
  const uid = React.useId().replace(/[^a-zA-Z0-9]/g, '');
  const lg1 = `lg1-${uid}`;
  const lg2 = `lg2-${uid}`;
  const lgb = `lgb-${uid}`;
  return (
    <Link
      to={to}
      className="inline-flex items-center gap-2.5 select-none transition-opacity hover:opacity-90"
      aria-label="Nuage Events"
    >
      <svg viewBox="0 0 64 64" width={size} height={size} aria-hidden="true">
        
  <defs>
    <linearGradient id="lgb" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#be2c88"/><stop offset="1" stop-color="#d160a7"/>
    </linearGradient>
    <linearGradient id="lg1" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#be2c88"/><stop offset="1" stop-color="#d160a7"/>
    </linearGradient>
    <linearGradient id="lg2" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#d160a7"/><stop offset="1" stop-color="#be2c88"/>
    </linearGradient>
  </defs>
  <rect width="64" height="64" rx="14" fill="url(`#${lgb}`)" opacity="0.12"/>
  <path d="M4 40 Q18 26 32 40 T60 40 V60 H4 Z" fill="url(lg1)" opacity=".95"/><path d="M4 50 Q18 36 32 50 T60 50 V60 H4 Z" fill="url(lg2)" opacity=".9"/>
  <rect x="42" y="8" width="16" height="16" rx="5" fill="url(`#${lgb}`)"/>
  <text x="50" y="20.5" text-anchor="middle" font-family="Trebuchet MS, sans-serif" font-size="12" font-weight="800" fill="#fff" letter-spacing="0.5">N</text>

      </svg>
      <span className="font-display font-bold tracking-tight leading-none">
        <span className={dark ? 'text-white' : 'text-slate-900'}>Nuage</span>
        <span className="bg-gradient-to-r from-primary to-accent-400 bg-clip-text text-transparent">
           Events
        </span>
      </span>
    </Link>
  );
}
