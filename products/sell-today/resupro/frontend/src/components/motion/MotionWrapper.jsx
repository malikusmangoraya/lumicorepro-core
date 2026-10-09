/**
 * MotionWrapper — Framer Motion wrapper configuration (TRD #3 motion profiles).
 * Cohesive duration/easing come from `motionPresets.js`.
 */
import { motion, useReducedMotion } from 'framer-motion';
import { DURATIONS, EASING, PRESETS } from '../../lib/motionPresets';

export default function MotionWrapper({
  variant = 'slide-up',
  duration = 'standard',
  className = '',
  children,
  ...props
}) {
  const reduce = useReducedMotion();
  const preset = PRESETS[variant] || PRESETS['slide-up'];
  return (
    <motion.div
      className={className}
      initial={reduce ? false : 'hidden'}
      whileInView="show"
      viewport={{ once: true, amount: 0.2 }}
      variants={preset}
      transition={{ duration: DURATIONS[duration] ?? DURATIONS.standard, ease: EASING }}
      {...props}
    >
      {children}
    </motion.div>
  );
}
