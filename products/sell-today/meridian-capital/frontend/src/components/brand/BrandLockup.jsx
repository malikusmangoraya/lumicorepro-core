import React from 'react';
import { Link } from 'react-router-dom';
import UniqueLogo from '../common/UniqueLogo';
import { BRAND } from './BRAND';

/** BrandLockup — mark + wordmark (layout-engine generated). */
export default function BrandLockup({ to = '/', size = 34, dark = false, className = '' }) {
  return (
    <Link to={to} className={`inline-flex items-center gap-2.5 select-none hover:opacity-90 ${className}`} aria-label={BRAND.name}>
      <UniqueLogo size={size} className="shrink-0" />
      <span className="font-bold tracking-tight leading-none whitespace-nowrap"
        style={{ fontFamily: `${BRAND.displayFont}, system-ui, sans-serif`, color: dark ? '#fff' : 'var(--t-heading)' }}>
        {BRAND.name}
      </span>
    </Link>
  );
}
