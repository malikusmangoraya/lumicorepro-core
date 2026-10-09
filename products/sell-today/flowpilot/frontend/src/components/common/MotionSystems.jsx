/**
 * MotionSystems — hover micro-states + reveal primitives (framer-motion).
 * Auto-generated utility — project primitive.
 * Respects prefers-reduced-motion.
 */
import { motion, useReducedMotion } from 'framer-motion';
import { useRef } from 'react';
import useInView from '../../hooks/useInView';

export function Reveal({ children, delay = 0, className = '' }) {
  const reduce = useReducedMotion();
  const [ref, inView] = useInView();
  return (
    <motion.div
      ref={ref}
      className={className}
      initial={reduce ? false : { opacity: 0, y: 24 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

export function MagneticButton({ children, strength = 0.35, className = '', ...props }) {
  const reduce = useReducedMotion();
  const ref = useRef(null);
  const onMove = (e) => {
    if (reduce || !ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const x = (e.clientX - rect.left - rect.width / 2) * strength;
    const y = (e.clientY - rect.top - rect.height / 2) * strength;
    ref.current.style.transform = `translate(${x}px, ${y}px)`;
  };
  const reset = () => {
    if (ref.current) ref.current.style.transform = 'translate(0, 0)';
  };
  return (
    <motion.button
      ref={ref}
      onMouseMove={onMove}
      onMouseLeave={reset}
      whileTap={{ scale: 0.97 }}
      className={`fluid-ease ${className}`}
      {...props}
    >
      {children}
    </motion.button>
  );
}

export function TiltCard({ children, max = 6, className = '' }) {
  const reduce = useReducedMotion();
  const ref = useRef(null);
  const onMove = (e) => {
    if (reduce || !ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const px = (e.clientX - rect.left) / rect.width - 0.5;
    const py = (e.clientY - rect.top) / rect.height - 0.5;
    ref.current.style.transform = `perspective(900px) rotateY(${px * max}deg) rotateX(${-py * max}deg)`;
  };
  const reset = () => {
    if (ref.current) ref.current.style.transform = '';
  };
  return (
    <motion.div
      ref={ref}
      onMouseMove={onMove}
      onMouseLeave={reset}
      className={`fluid-ease ${className}`}
    >
      {children}
    </motion.div>
  );
}

export function HoverGlow({ className = '', children }) {
  return (
    <div className={`group relative overflow-hidden ${className}`}>
      <div className="pointer-events-none absolute -inset-px opacity-0 transition-opacity duration-300 group-hover:opacity-100 bg-[radial-gradient(400px_circle_at_var(--x,50%)_var(--y,50%),rgba(6,182,212,0.18),transparent_60%)]" />
      {children}
    </div>
  );
}

export default function MotionSystems() {
  return null;
}
