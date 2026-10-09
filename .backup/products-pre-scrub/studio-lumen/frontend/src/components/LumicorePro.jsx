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
      aria-label="Studio Lumen"
    >
      <svg viewBox="0 0 64 64" width={size} height={size} aria-hidden="true">
        
  <defs>
    <linearGradient id="lgb" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#be662c"/><stop offset="1" stop-color="#d18d60"/>
    </linearGradient>
    <linearGradient id="lg1" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#be662c"/><stop offset="1" stop-color="#d18d60"/>
    </linearGradient>
    <linearGradient id="lg2" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#d18d60"/><stop offset="1" stop-color="#be662c"/>
    </linearGradient>
  </defs>
  <rect width="64" height="64" rx="14" fill="url(`#${lgb}`)" opacity="0.12"/>
  <circle cx="32" cy="32" r="20" fill="none" stroke="url(lg1)" stroke-width="4"/><ellipse cx="32" cy="32" rx="14" ry="30" fill="none" stroke="url(lg2)" stroke-width="3" transform="rotate(-28 32 32)"/><circle cx="46" cy="12" r="5" fill="url(lg2)"/>
  <rect x="42" y="8" width="16" height="16" rx="5" fill="url(`#${lgb}`)"/>
  <text x="50" y="20.5" text-anchor="middle" font-family="Trebuchet MS, sans-serif" font-size="12" font-weight="800" fill="#fff" letter-spacing="0.5">S</text>

      </svg>
      <span className="font-display font-bold tracking-tight leading-none">
        <span className={dark ? 'text-white' : 'text-slate-900'}>Studio</span>
        <span className="bg-gradient-to-r from-primary to-accent-400 bg-clip-text text-transparent">
           Lumen
        </span>
      </span>
    </Link>
  );
}
