import Link from 'next/link';

/**
 * Apex mark — an "A" shaped like a road converging to a vanishing point.
 * Two gradient strokes, a dashed centre line for the crossbar, and a horizon
 * split beneath. Drawn as geometry rather than text so it stays crisp at
 * 16px (favicon) and 96px (hero) with the same file.
 */
export function BrandMark({
  size = 32,
  className,
  id = 'apex-mark',
}: {
  size?: number;
  className?: string;
  id?: string;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      role="img"
      aria-label="Apex Motor Collective mark"
      className={className}
    >
      <defs>
        <linearGradient id={`${id}-badge`} x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#191026" />
          <stop offset="0.55" stopColor="#0d1220" />
          <stop offset="1" stopColor="#0a0f1a" />
        </linearGradient>
        <linearGradient id={`${id}-stroke`} x1="14" y1="50" x2="50" y2="14" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#9f28d9" />
          <stop offset="0.5" stopColor="#b75cf6" />
          <stop offset="1" stopColor="#e284fc" />
        </linearGradient>
        <linearGradient id={`${id}-edge`} x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#e284fc" stopOpacity="0.55" />
          <stop offset="1" stopColor="#9f28d9" stopOpacity="0.12" />
        </linearGradient>
      </defs>

      <rect x="1" y="1" width="62" height="62" rx="17" fill={`url(#${id}-badge)`} />
      <rect
        x="1.75"
        y="1.75"
        width="60.5"
        height="60.5"
        rx="16.25"
        fill="none"
        stroke={`url(#${id}-edge)`}
        strokeWidth="1.5"
      />

      {/* The road: two edges rising to the apex */}
      <path
        d="M15.5 50 L32 15.5 L48.5 50"
        fill="none"
        stroke={`url(#${id}-stroke)`}
        strokeWidth="5.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Centre line — dashed, like lane markings */}
      <path
        d="M26.4 38.5 h11.2"
        fill="none"
        stroke="#0d1220"
        strokeWidth="3.2"
        strokeLinecap="round"
      />
      <path
        d="M23.5 43.5 h17"
        fill="none"
        stroke={`url(#${id}-stroke)`}
        strokeWidth="2.1"
        strokeLinecap="round"
        opacity="0.55"
      />
      {/* Horizon split at the apex */}
      <path d="M27.6 22.4 h8.8" stroke="#e0f2fe" strokeWidth="2" strokeLinecap="round" opacity="0.9" />
    </svg>
  );
}

export function BrandLockup({ compact = false }: { compact?: boolean }) {
  return (
    <Link
      href="/"
      className="group flex items-center gap-2.5"
      aria-label="Apex Motor Collective — home"
    >
      <span className="transition-transform duration-300 group-hover:-translate-y-0.5">
        <BrandMark size={compact ? 30 : 34} />
      </span>
      <span className="flex flex-col leading-none">
        <span
          className="font-display text-[1.08rem] font-800 tracking-[-0.01em] text-heading"
          style={{ letterSpacing: '-0.01em' }}
        >
          APEX
        </span>
        {!compact && (
          <span className="mt-0.5 text-[0.58rem] font-semibold uppercase tracking-[0.28em] text-muted">
            Motor Collective
          </span>
        )}
      </span>
    </Link>
  );
}
