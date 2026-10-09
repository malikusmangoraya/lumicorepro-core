import React from 'react';
import { Link } from 'react-router-dom';

export const LOGO_SYMBOLS = [
  {
    name: 'hexa',
    paths: {
      outer: '24,4 42,14 42,34 24,44 6,34 6,14',
      mid: '24,12 34,18 34,30 24,36 14,30 14,18',
      inner: '24,18 29,21 29,27 24,30 19,27 19,21',
    },
  },
  {
    name: 'diamond',
    paths: {
      outer: '24,2 46,24 24,46 2,24',
      mid: '24,12 36,24 24,36 12,24',
      inner: '24,19 29,24 24,29 19,24',
    },
  },
  {
    name: 'plus',
    paths: {
      outer: '24,2 36,12 46,24 36,36 24,46 12,36 2,24 12,12',
      mid: '24,14 32,22 40,24 32,26 24,34 16,26 8,24 16,22',
      inner: '24,19 28,23 32,24 28,25 24,29 20,25 16,24 20,23',
    },
  },
];

export default function UniqueLogo({ name = 'LuminaCore', size = 'md' }) {
  const sz = { sm: 24, md: 32, lg: 40 }[size] || 32;
  const words = name.split(/(?=[A-Z])|\s+/).filter(Boolean);
  const primaryWord = words[0] || name;
  const accentWord = words.slice(1).join('') || '';

  return (
    <Link
      to="/"
      className="inline-flex items-center gap-2.5 select-none transition-opacity hover:opacity-90"
    >
      <svg viewBox="0 0 48 48" width={sz} height={sz} className="shrink-0" fill="none">
        <defs>
          <linearGradient id="brand-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="rgb(6, 182, 212)" />
            <stop offset="100%" stopColor="rgb(139, 92, 246)" />
          </linearGradient>
        </defs>
        <polygon points="24,4 42,14 42,34 24,44 6,34 6,14" fill="url(#brand-grad)" opacity="0.95" />
        <polygon points="24,12 34,18 34,30 24,36 14,30 14,18" fill="white" opacity="0.9" />
        <polygon points="24,18 29,21 29,27 24,30 19,27 19,21" fill="url(#brand-grad)" />
      </svg>
      <span className="font-extrabold text-xl tracking-tight text-white font-sans">
        {primaryWord}
        {accentWord && (
          <span className="bg-gradient-to-r from-cyan-400 to-violet-500 bg-clip-text text-transparent ml-0.5">
            {accentWord}
          </span>
        )}
      </span>
    </Link>
  );
}
