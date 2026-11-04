import React from 'react';

export default function UniqueLogo({ size = "w-8 h-8", className = "" }) {
  return (
    <div className={`inline-flex items-center justify-center ${size} ${className}`}>
      <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
        <defs>
          <linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#8b5cf6" />
            <stop offset="100%" stopColor="#c084fc" />
          </linearGradient>
        </defs>
        <polygon points="24,4 40,14 40,34 24,44 8,34 8,14" fill="none" stroke="url(#logoGrad)" strokeWidth="3" />
        <circle cx="24" cy="24" r="5" fill="#c084fc" />
        <line x1="24" y1="4" x2="24" y2="19" stroke="url(#logoGrad)" strokeWidth="2" />
        <line x1="40" y1="34" x2="27" y2="26" stroke="url(#logoGrad)" strokeWidth="2" />
        <line x1="8" y1="34" x2="21" y2="26" stroke="url(#logoGrad)" strokeWidth="2" />
      </svg>
    </div>
  );
}
