import React, { useRef, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/utils';

export function HolographicCard({
  children,
  className = '',
  glareOpacity = 0.35,
  neonColor = '#06b6d4', // cyan
  accentColor = '#8b5cf6', // violet
  scaleOnHover = 1.02,
  ...props
}) {
  const cardRef = useRef(null);
  const [rotateX, setRotateX] = useState(0);
  const [rotateY, setRotateY] = useState(0);
  const [glarePosition, setGlarePosition] = useState({ x: 50, y: 50 });
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = useCallback((e) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotX = -((y - centerY) / centerY) * 12; // max 12 deg
    const rotY = ((x - centerX) / centerX) * 12;

    setRotateX(rotX);
    setRotateY(rotY);
    setGlarePosition({
      x: (x / rect.width) * 100,
      y: (y / rect.height) * 100,
    });
  }, []);

  const handleMouseEnter = useCallback(() => setIsHovered(true), []);
  const handleMouseLeave = useCallback(() => {
    setIsHovered(false);
    setRotateX(0);
    setRotateY(0);
  }, []);

  return (
    <div style={{ perspective: '1200px' }} className="w-full">
      <motion.div
        ref={cardRef}
        onMouseMove={handleMouseMove}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        animate={{
          rotateX,
          rotateY,
          scale: isHovered ? scaleOnHover : 1,
        }}
        transition={{
          type: 'spring',
          stiffness: 250,
          damping: 25,
        }}
        style={{
          transformStyle: 'preserve-3d',
        }}
        className={cn(
          'relative overflow-hidden rounded-2xl border border-white/10 bg-slate-950/80 p-6 shadow-2xl backdrop-blur-xl transition-shadow duration-300',
          'hover:border-cyan-500/40 hover:shadow-cyan-500/10',
          className
        )}
        {...props}
      >
        {/* Holographic Rainbow Sheen */}
        <div
          className="pointer-events-none absolute inset-0 mix-blend-color-dodge transition-opacity duration-300"
          style={{
            opacity: isHovered ? glareOpacity : 0,
            background: `linear-gradient(135deg, 
              rgba(255, 0, 150, 0.25) 0%, 
              rgba(0, 204, 255, 0.25) 25%, 
              rgba(255, 221, 0, 0.2) 50%, 
              rgba(115, 0, 255, 0.25) 75%, 
              rgba(0, 255, 170, 0.25) 100%)`,
            backgroundPosition: `${glarePosition.x}% ${glarePosition.y}%`,
            backgroundSize: '200% 200%',
          }}
          aria-hidden="true"
        />

        {/* Dynamic Light Specular Glare */}
        <div
          className="pointer-events-none absolute inset-0 transition-opacity duration-300"
          style={{
            opacity: isHovered ? 0.6 : 0,
            background: `radial-gradient(circle at ${glarePosition.x}% ${glarePosition.y}%, rgba(255,255,255,0.3) 0%, transparent 60%)`,
          }}
          aria-hidden="true"
        />

        {/* Content with preserve-3d offset */}
        <div style={{ transform: 'translateZ(30px)' }} className="relative z-10">
          {children}
        </div>
      </motion.div>
    </div>
  );
}

export default HolographicCard;
