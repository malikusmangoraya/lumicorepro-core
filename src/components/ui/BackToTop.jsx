import { useEffect, useState } from 'react';
import { ArrowUp } from 'lucide-react';
import { cn } from '../../utils';
import useReducedMotion from '../../hooks/useReducedMotion';

/**
 * Floating back-to-top button, bottom-right.
 *
 * - Stays mounted (so it can fade) but is `invisible` while hidden, which
 *   removes it from the accessibility tree and the tab order automatically.
 * - `position: fixed` → zero layout shift; only transform/opacity animate.
 * - Honours `prefers-reduced-motion`: the jump to top is instant instead of
 *   a smooth scroll.
 */
export default function BackToTop({ threshold = 400, className = '' }) {
  const [visible, setVisible] = useState(false);
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    let frame = null;
    const raf =
      typeof window.requestAnimationFrame === 'function'
        ? window.requestAnimationFrame.bind(window)
        : (cb) => setTimeout(cb, 16);
    const caf =
      typeof window.cancelAnimationFrame === 'function'
        ? window.cancelAnimationFrame.bind(window)
        : clearTimeout;

    const onScroll = () => {
      if (frame !== null) return;
      frame = raf(() => {
        frame = null;
        setVisible(window.scrollY > threshold);
      });
    };

    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', onScroll);
      if (frame !== null) caf(frame);
    };
  }, [threshold]);

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: reducedMotion ? 'auto' : 'smooth' });
  };

  return (
    <button
      type="button"
      onClick={scrollToTop}
      aria-label="Back to top"
      title="Back to top"
      className={cn(
        'fixed bottom-6 right-6 z-50 inline-flex h-10 w-10 items-center justify-center rounded-full',
        'bg-primary text-primary-foreground shadow-lg ring-1 ring-black/5',
        'transition-all duration-200 hover:scale-105',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/40',
        'motion-reduce:transition-none motion-reduce:hover:scale-100',
        visible
          ? 'visible translate-y-0 opacity-100'
          : 'invisible pointer-events-none translate-y-3 opacity-0',
        className
      )}
    >
      <ArrowUp className="h-5 w-5" aria-hidden="true" />
    </button>
  );
}
