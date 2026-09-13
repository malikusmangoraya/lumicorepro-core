import React from 'react';
import { Link } from 'react-router-dom';

export default function UniqueLogo({ size = 'md' }) {
  const sz = { sm: 24, md: 32, lg: 40 }[size] || 32;
  return (
    <Link to="/" className="inline-flex items-center gap-2.5 select-none transition-opacity hover:opacity-90">
      <div style={{ width: sz, height: sz }} className="shrink-0">
        <svg viewBox="0 0 48 48" width="100%" height="100%" fill="none" xmlns="http://www.w3.org/2000/svg"><polygon points="24,4 44,20 38,44 10,44 4,20" fill="#dc2626" opacity="0.95"/><polygon points="24,14 34,22 31,36 17,36 14,22" fill="white" opacity="0.9"/><polygon points="24,20 28,23 27,29 21,29 20,23" fill="#f59e0b"/></svg>
      </div>
      <span className="font-extrabold text-xl tracking-tight" style={{ color: '#1f2937' }}>
        FoodExpress 
      </span>
    </Link>
  );
}
