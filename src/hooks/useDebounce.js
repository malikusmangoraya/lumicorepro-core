import { useState, useEffect } from 'react';

/**
 * Debounce a changing value.
 * @param {*} value
 * @param {number} delay
 */
export default function useDebounce(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);

  return debounced;
}
