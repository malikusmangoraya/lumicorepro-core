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
      aria-label="Aurelia Estates"
    >
      <svg viewBox="0 0 64 64" width={size} height={size} aria-hidden="true">
        
  <defs>
    <linearGradient id="lgb" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#be882c"/><stop offset="1" stop-color="#d1a760"/>
    </linearGradient>
    <linearGradient id="lg1" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#be882c"/><stop offset="1" stop-color="#d1a760"/>
    </linearGradient>
    <linearGradient id="lg2" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#d1a760"/><stop offset="1" stop-color="#be882c"/>
    </linearGradient>
  </defs>
  <rect width="64" height="64" rx="14" fill="url(`#${lgb}`)" opacity="0.12"/>
  <path d="M36 4 L14 36 L28 36 L24 60 L50 26 L34 26 Z" fill="url(lg1)"/><path d="M36 4 L14 36 L28 36 L24 60 L50 26 L34 26 Z" fill="none" stroke="url(lg2)" stroke-width="1.5"/>
  <rect x="42" y="8" width="16" height="16" rx="5" fill="url(`#${lgb}`)"/>
  <text x="50" y="20.5" text-anchor="middle" font-family="Trebuchet MS, sans-serif" font-size="12" font-weight="800" fill="#fff" letter-spacing="0.5">A</text>

      </svg>
      <span className="font-display font-bold tracking-tight leading-none">
        <span className={dark ? 'text-white' : 'text-slate-900'}>Aurelia</span>
        <span className="bg-gradient-to-r from-primary to-accent-400 bg-clip-text text-transparent">
           Estates
        </span>
      </span>
    </Link>
  );
}
