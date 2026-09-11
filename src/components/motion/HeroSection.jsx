import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../utils';

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i = 0) => ({
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.6,
      delay: i * 0.12,
      ease: [0.22, 1, 0.36, 1],
    },
  }),
};

const blobs = [
  {
    className: 'bg-primary/20',
    size: 'h-72 w-72',
    pos: 'top-10 left-[8%]',
    animate: { x: [0, 30, -20, 0], y: [0, -25, 15, 0] },
    duration: 14,
  },
  {
    className: 'bg-violet-500/15',
    size: 'h-64 w-64',
    pos: 'bottom-8 right-[10%]',
    animate: { x: [0, -25, 20, 0], y: [0, 20, -15, 0] },
    duration: 18,
  },
  {
    className: 'bg-cyan-500/10',
    size: 'h-56 w-56',
    pos: 'top-1/2 left-1/2 -translate-x-1/2',
    animate: { x: [0, 15, -15, 0], y: [0, -10, 10, 0] },
    duration: 22,
  },
];

const HeroSection = ({ children, className = '' }) => {
  return (
    <section aria-label="Hero" className={cn('relative overflow-hidden', className)}>
      {/* Gradient mesh background */}
      <div className="pointer-events-none absolute inset-0 bg-gradient-mesh" aria-hidden="true" />

      {/* Animated blobs */}
      {blobs.map((blob, i) => (
        <motion.div
          key={i}
          className={cn(
            'pointer-events-none absolute rounded-full blur-3xl',
            blob.size,
            blob.pos,
            blob.className
          )}
          animate={blob.animate}
          transition={{
            duration: blob.duration,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
          aria-hidden="true"
        />
      ))}

      {/* Glass card content wrapper */}
      <div className="relative z-10">
        <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={0}>
          {children}
        </motion.div>
      </div>
    </section>
  );
};

export function HeroTitle({ children, className = '' }) {
  return (
    <motion.h1
      variants={fadeUp}
      initial="hidden"
      animate="visible"
      custom={1}
      className={cn(
        'font-display text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.05] gradient-text',
        className
      )}
    >
      {children}
    </motion.h1>
  );
}

export function HeroSubtitle({ children, className = '' }) {
  return (
    <motion.p
      variants={fadeUp}
      initial="hidden"
      animate="visible"
      custom={2}
      className={cn(
        'mt-6 max-w-2xl mx-auto text-lg text-muted-foreground leading-relaxed',
        className
      )}
    >
      {children}
    </motion.p>
  );
}

export function HeroActions({ children, className = '' }) {
  return (
    <motion.div
      variants={fadeUp}
      initial="hidden"
      animate="visible"
      custom={3}
      className={cn('mt-8 flex flex-col sm:flex-row items-center justify-center gap-3', className)}
    >
      {children}
    </motion.div>
  );
}

export function HeroTrust({ children, className = '' }) {
  return (
    <motion.div
      variants={fadeUp}
      initial="hidden"
      animate="visible"
      custom={4}
      className={cn(
        'mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-muted-foreground',
        className
      )}
    >
      {children}
    </motion.div>
  );
}

export default HeroSection;
