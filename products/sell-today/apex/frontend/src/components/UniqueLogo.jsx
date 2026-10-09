// Apex Digital logo wrapper. The artwork lives in ./brand/BrandMark.jsx.
import React from 'react';
import BrandLockup from './brand/BrandLockup';

const SIZES = { sm: 24, md: 32, lg: 40 };

export default function UniqueLogo({ size = 'md' }) {
  return <BrandLockup size={SIZES[size] || SIZES.md} />;
}
