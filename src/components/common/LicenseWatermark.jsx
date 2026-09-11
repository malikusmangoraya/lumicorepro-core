import React from 'react';
import useLicense from '../../hooks/useLicense';

/**
 * LicenseWatermark — trial-mode watermark (self-hosted, free).
 *
 * Renders a fixed, low-opacity brand strip whenever no valid (paid) license
 * is present, exactly like a trial watermark. Hides itself once a full
 * license is activated. Respects prefers-reduced-motion.
 */
export default function LicenseWatermark({ product = 'LumicorePro', onActivate }) {
  const { valid, trial, status } = useLicense();
  const show = !valid && trial && status !== 'no_key';
  if (!show) return null;

  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed bottom-2 right-2 z-[9999] rounded-md border border-amber-500/40 bg-amber-500/10 px-2.5 py-1 text-[10px] font-medium tracking-wide text-amber-700 dark:text-amber-400 backdrop-blur-sm transition-all duration-200"
    >
      {product} · Trial Mode
      {onActivate ? (
        <button
          type="button"
          aria-hidden="true"
          tabIndex={-1}
          className="pointer-events-auto ml-2 rounded border border-amber-500/50 px-1.5 py-0.5 text-[10px] hover:bg-amber-500/20"
          onClick={onActivate}
        >
          Activate
        </button>
      ) : null}
    </div>
  );
}