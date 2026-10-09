import React from 'react';

const GID = 'lc-prism-grad';

const GRAD = (
  <defs>
    <linearGradient id={GID} x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stopColor="#ffd9a0" />
      <stop offset="42%" stopColor="#e2b26b" />
      <stop offset="100%" stopColor="#7a4fd0" />
    </linearGradient>
    <radialGradient id="lc-glow" cx="50%" cy="42%" r="55%">
      <stop offset="0%" stopColor="#fff8ec" />
      <stop offset="55%" stopColor="#ffd9a0" />
      <stop offset="100%" stopColor="#7a4fd0" />
    </radialGradient>
  </defs>
);

function Rays() {
  const idx = [8, 5, 2, -1, -4];
  return (
    <g stroke="url(#lc-glow)" strokeWidth="1.6" strokeLinecap="round" opacity="0.85">
      {idx.map((d) => (
        <line key={d} x1="24" y1="4.5" x2="24" y2={String(14 + d)} />
      ))}
      {idx.map((d) => (
        <line key={d + 50} x1="4.5" y1="24" x2={String(14 + d)} y2="24" />
      ))}
      {idx.map((d) => (
        <line key={d + 9} x1="24" y1="43.5" x2="24" y2={String(34 - d)} />
      ))}
    </g>
  );
}

function Prism() {
  return (
    <g>
      <path
        d="M24 3 L43 14 L43 34 L24 45 L5 34 L5 14 Z"
        fill="url(#lc-prism-grad)"
        opacity="0.22"
      />
      <path
        d="M24 3 L43 14 L43 34 L24 45 L5 34 L5 14 Z"
        fill="none"
        stroke="#ffd9a0"
        strokeWidth="2"
        opacity="0.95"
      />
      <path
        d="M24 13 L36 19.8 L36 28.2 L24 35 L12 28.2 L12 19.8 Z"
        fill="none"
        stroke="#fff"
        strokeOpacity="0.9"
        strokeWidth="1.4"
      />
      <circle cx="24" cy="24" r="6.4" fill="url(#lc-glow)" />
      <path
        d="M20.8 24 h6.4 M24 20.8 v6.4"
        stroke="#241a3d"
        strokeWidth="1.1"
        strokeLinecap="round"
        opacity="0.8"
      />
    </g>
  );
}

export function LogoMark({ size = 30, className = '' }) {
  return (
    <svg
      viewBox="0 0 48 48"
      width={size}
      height={size}
      className={className}
      fill="none"
      aria-hidden="true"
    >
      {GRAD}
      <Rays />
      <Prism />
    </svg>
  );
}

export default function BrandLogo({ size = 'md', className = '' }) {
  const sz = { sm: 22, md: 30, lg: 40 }[size] || 30;
  return <LogoMark size={sz} className={className} />;
}

export { GID };
