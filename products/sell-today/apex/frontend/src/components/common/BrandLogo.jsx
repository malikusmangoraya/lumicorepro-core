// Apex Digital logo wrapper. The artwork lives in ./brand/BrandMark.jsx.
import React from 'react';
import { BrandMark } from '../brand/BrandMark';

const SIZES = { sm: 24, md: 30, lg: 40 };

export function LogoMark({ size = 30, className = '' }) {
  return <BrandMark size={size} className={className} />;
}

export default function BrandLogo({ size = 'md', className = '' }) {
  return <LogoMark size={SIZES[size] || SIZES.md} className={className} />;
}
