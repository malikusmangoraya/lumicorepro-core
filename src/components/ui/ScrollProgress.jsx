import useScrollProgress from '../../hooks/useScrollProgress';

/**
 * Thin reading-progress bar pinned to the top of the viewport.
 *
 * Layout-safe by construction: the bar is `position: fixed`, so mounting it
 * can never shift page content (this app has a CLS < 0.1 hard gate, and a
 * footer that mounted visible once cost 0.34 CLS). Only `transform` is
 * animated, and the transition is disabled under `prefers-reduced-motion`.
 */
export default function ScrollProgress({ className = '' }) {
  const progress = useScrollProgress();

  return (
    <div
      aria-hidden="true"
      className={`pointer-events-none fixed inset-x-0 top-0 z-[60] h-0.5 bg-transparent ${className}`}
    >
      <div
        className="h-full origin-left bg-primary transition-transform duration-150 ease-out motion-reduce:transition-none"
        style={{ transform: `scaleX(${progress})` }}
      />
    </div>
  );
}
