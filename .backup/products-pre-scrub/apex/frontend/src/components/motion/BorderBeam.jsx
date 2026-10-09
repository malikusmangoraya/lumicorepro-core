import React from 'react';
import { motion } from 'framer-motion';

export default function BorderBeam({
  children,
  className = '',
  color = 'from-cyan-500 to-violet-500',
  speed = 3,
  ...props
}) {
  return (
    <div className={`relative ${className}`} {...props}>
      <motion.div
        className="absolute inset-0 rounded-2xl"
        style={{
          border: '2px solid transparent',
          background: `linear-gradient(90deg, ${color.replace('to', 'to')}) border-box`,
          WebkitMask: 'linear-gradient(white, white) padding-box, linear-gradient(white, white)',
          WebkitMaskComposite: 'xor',
          maskComposite: 'exclude',
        }}
        animate={{ backgroundPosition: ['0%', '200%', '0%'] }}
        transition={{ duration: speed, repeat: Infinity, ease: 'linear' }}
      />
      <div className="relative z-10 rounded-2xl bg-slate-950/80 backdrop-blur-xl p-6 h-full">
        {children}
      </div>
    </div>
  );
}
