'use client';

import { useEffect, useState } from 'react';
import { ArrowUp } from 'lucide-react';

export function BackToTop() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const onScroll = () => setVisible(window.scrollY > 700);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <button
      type="button"
      aria-label="Back to top"
      onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
      className={
        visible
          ? 'fixed bottom-5 right-5 z-40 inline-flex size-11 items-center justify-center rounded-full border border-line bg-surface/90 text-heading shadow-lg backdrop-blur transition-opacity hover:border-primary/60'
          : 'pointer-events-none fixed bottom-5 right-5 z-40 inline-flex size-11 items-center justify-center rounded-full border border-line bg-surface/90 text-heading opacity-0 transition-opacity'
      }
    >
      <ArrowUp className="size-4" aria-hidden="true" />
    </button>
  );
}
