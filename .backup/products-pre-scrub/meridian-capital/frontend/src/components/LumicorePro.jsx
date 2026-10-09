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
      aria-label="Meridian Capital"
    >
      <svg viewBox="0 0 64 64" width={size} height={size} aria-hidden="true">
        
  <defs>
    <linearGradient id="lgb" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#2cbe7e"/><stop offset="1" stop-color="#60d1a0"/>
    </linearGradient>
    <linearGradient id="lg1" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#2cbe7e"/><stop offset="1" stop-color="#60d1a0"/>
    </linearGradient>
    <linearGradient id="lg2" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#60d1a0"/><stop offset="1" stop-color="#2cbe7e"/>
    </linearGradient>
  </defs>
  <rect width="64" height="64" rx="14" fill="url(`#${lgb}`)" opacity="0.12"/>
  <rect x="8" y="22" width="9" height="34" fill="url(lg2)"/><rect x="21" y="12" width="9" height="44" fill="url(lg1)"/><rect x="34" y="26" width="9" height="30" fill="url(lg2)"/><rect x="47" y="8" width="9" height="48" fill="url(lg1)"/><path d="M4 56 H60" stroke="url(lg1)" stroke-width="3"/>
  <rect x="42" y="8" width="16" height="16" rx="5" fill="url(`#${lgb}`)"/>
  <text x="50" y="20.5" text-anchor="middle" font-family="Trebuchet MS, sans-serif" font-size="12" font-weight="800" fill="#fff" letter-spacing="0.5">M</text>

      </svg>
      <span className="font-display font-bold tracking-tight leading-none">
        <span className={dark ? 'text-white' : 'text-slate-900'}>Meridian</span>
        <span className="bg-gradient-to-r from-primary to-accent-400 bg-clip-text text-transparent">
           Capital
        </span>
      </span>
    </Link>
  );
}
