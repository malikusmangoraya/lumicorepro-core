// Apex Digital logo wrapper. The artwork lives in ./brand/BrandMark.jsx.
import React from 'react';
import { Link } from 'react-router-dom';
import { BrandMark } from '../brand/BrandMark';
import { BRAND } from '../brand/BRAND';

const SIZES = { sm: 24, md: 32, lg: 40 };

export const LOGO_SYMBOLS = [BRAND];

export default function UniqueLogo({ name, size = 'md', className = '' }) {
  const px = SIZES[size] || SIZES.md;
  const label = name || BRAND.name;
  return (
    <Link
      to="/"
      className={`inline-flex items-center gap-2.5 select-none ${className}`}
      aria-label={label}
    >
      <BrandMark size={px} className="shrink-0" />
      <span className="font-bold tracking-tight whitespace-nowrap">{label}</span>
    </Link>
  );
}
