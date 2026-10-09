import { useEffect, useState } from 'react';

const QUERY = '(prefers-reduced-motion: reduce)';

function readsReducedMotion() {
  return (
    typeof window !== 'undefined' &&
    typeof window.matchMedia === 'function' &&
    window.matchMedia(QUERY).matches
  );
}

/**
 * Tracks the OS-level `prefers-reduced-motion` setting, live.
 *
 * Every animated component must branch on this: reduced-motion users get the
 * static version of the effect, not a slowed-down one. Returns `false` when
 * the API is unavailable (jsdom, very old browsers) so callers keep rendering.
 */
export default function useReducedMotion() {
  const [reduced, setReduced] = useState(readsReducedMotion);

  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
      return undefined;
    }
    const mediaQuery = window.matchMedia(QUERY);
    const onChange = (event) => setReduced(event.matches);
    setReduced(mediaQuery.matches);

    // Safari < 14 only implements the deprecated add/removeListener pair.
    if (typeof mediaQuery.addEventListener === 'function') {
      mediaQuery.addEventListener('change', onChange);
      return () => mediaQuery.removeEventListener('change', onChange);
    }
    mediaQuery.addListener(onChange);
    return () => mediaQuery.removeListener(onChange);
  }, []);

  return reduced;
}
