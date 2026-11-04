import Link from 'next/link';

/**
 * Brand mark: a geometric "A" cut from two planes, in the brand gradient.
 * Rendered inline so it costs one request less and stays crisp at any size.
 */
export function BrandMark({ size = 32, className }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      role="img"
      aria-label="Apex Motor Collective mark"
      className={className}
    >
      <defs>
        <linearGradient id="apex-mark" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#b75cf6" />
          <stop offset="0.55" stopColor="#9f28d9" />
          <stop offset="1" stopColor="#e284fc" />
        </linearGradient>
      </defs>
      <rect width="48" height="48" rx="12" fill="#0d1220" />
      <path d="M24 10 38 38h-8.2L24 25.4 18.2 38H10L24 10Z" fill="url(#apex-mark)" />
      <path d="M24 30.2 27.4 38h-6.8L24 30.2Z" fill="#e0f2fe" opacity="0.85" />
    </svg>
  );
}

export function BrandLockup({ compact = false }: { compact?: boolean }) {
  return (
    <Link href="/" className="group flex items-center gap-2.5" aria-label="Apex Motor Collective — home">
      <BrandMark size={compact ? 28 : 32} />
      <span className="flex flex-col leading-none">
        <span className="font-display text-[1.05rem] font-700 tracking-tight text-heading">
          Apex
        </span>
        {!compact && (
          <span className="text-[0.62rem] font-medium uppercase tracking-[0.22em] text-muted">
            Motor Collective
          </span>
        )}
      </span>
    </Link>
  );
}
