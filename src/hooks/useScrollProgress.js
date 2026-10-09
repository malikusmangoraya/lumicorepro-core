import { useEffect, useState } from 'react';

const raf =
  typeof window !== 'undefined' && typeof window.requestAnimationFrame === 'function'
    ? window.requestAnimationFrame.bind(window)
    : (cb) => setTimeout(cb, 16);

const caf =
  typeof window !== 'undefined' && typeof window.cancelAnimationFrame === 'function'
    ? window.cancelAnimationFrame.bind(window)
    : clearTimeout;

function readProgress() {
  const doc = document.documentElement;
  const scrollable = doc.scrollHeight - doc.clientHeight;
  if (scrollable <= 0) return 0;
  const scrolled = window.scrollY || doc.scrollTop || 0;
  return Math.min(1, Math.max(0, scrolled / scrollable));
}

/**
 * Reading progress of the page: 0 at the top, 1 at the bottom (0 when the
 * page is not scrollable at all).
 *
 * Scroll events are coalesced into one rAF callback per frame, so a progress
 * bar driven by this hook never triggers layout thrash. The listener is
 * `passive`, so scrolling is never blocked waiting on the handler.
 */
export default function useScrollProgress() {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    let frame = null;
    const update = () => {
      frame = null;
      setProgress(readProgress());
    };
    const onScroll = () => {
      if (frame !== null) return;
      frame = raf(update);
    };

    update();
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onScroll);
      if (frame !== null) caf(frame);
    };
  }, []);

  return progress;
}
