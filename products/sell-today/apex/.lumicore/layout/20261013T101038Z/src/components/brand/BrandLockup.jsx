import React from 'react';
import { Link } from 'react-router-dom';
import { BrandMark } from './BrandMark';
import { BRAND } from './BRAND';

/** Mark + wordmark lockup used in the navbar and footer. */
export default function BrandLockup({ to = '/', size = 34, dark = false, className = '' }) {
  return (
    <Link
      to={to}
      className={`inline-flex items-center gap-2.5 select-none transition-opacity hover:opacity-90 ${className}`}
      aria-label={BRAND.name}
    >
      <BrandMark size={size} className="shrink-0" />
      <span
        className="font-bold tracking-tight leading-none whitespace-nowrap"
        style={{
          fontFamily: `${BRAND.displayFont}, system-ui, -apple-system, 'Segoe UI', sans-serif`,
          color: dark ? '#ffffff' : 'var(--t-heading, inherit)',
        }}
      >
        {BRAND.name}
      </span>
    </Link>
  );
}
