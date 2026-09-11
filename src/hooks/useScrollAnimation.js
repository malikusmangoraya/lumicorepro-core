import { useRef } from 'react';
import { useInView } from 'framer-motion';

export default function useScrollAnimation(options = {}) {
  const { margin = '-40px', once = true, amount = 0.1 } = options;
  const ref = useRef(null);
  const inView = useInView(ref, { margin, once, amount });
  return { ref, inView };
}
