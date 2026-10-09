import React from 'react';
import { motion } from 'framer-motion';

export default function HolographicCard({ children, className = '', borderWidth = 2, ...props }) {
  return (
    <motion.div
      className={`relative overflow-hidden rounded-2xl ${className}`}
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] }}
      {...props}
    >
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-cyan-500/20 via-transparent to-violet-500/20" />
      <div
        className="absolute inset-0 rounded-2xl border border-transparent"
        style={{ borderWidth }}
      >
        <div
          className="absolute inset-0 rounded-2xl bg-gradient-to-r from-cyan-500 to-violet-500"
          style={{
            mask: `linear-gradient(white, white) content-box, linear-gradient(white, white)`,
            WebkitMask: `linear-gradient(white, white) content-box, linear-gradient(white, white)`,
            maskComposite: 'exclude',
            WebkitMaskComposite: 'xor',
            borderWidth,
          }}
        />
      </div>
      <div className="relative z-10 bg-slate-950/80 backdrop-blur-xl rounded-[calc(0.75rem-2px)] p-6 h-full">
        {children}
      </div>
      <motion.div
        className="absolute inset-0 rounded-2xl"
        style={{
          border: `${borderWidth}px solid transparent`,
          background:
            'linear-gradient(90deg, var(--t-accent), var(--t-primary), var(--t-heading), var(--t-accent)) border-box',
          WebkitMask: 'linear-gradient(white, white) padding-box, linear-gradient(white, white)',
          WebkitMaskComposite: 'xor',
          maskComposite: 'exclude',
        }}
        animate={{ backgroundPosition: ['0%', '200%', '0%'] }}
        transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
      />
    </motion.div>
  );
}
