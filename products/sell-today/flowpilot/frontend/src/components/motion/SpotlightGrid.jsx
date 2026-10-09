import React, { useRef, useEffect, useState } from 'react';
import { motion } from 'framer-motion';

export default function SpotlightGrid({ children, className = '', intensity = 0.4, radius = 300 }) {
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const containerRef = useRef(null);

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setMousePos({
          x: e.clientX - rect.left,
          y: e.clientY - rect.top,
        });
      }
    };

    const container = containerRef.current;
    container.addEventListener('mousemove', handleMouseMove);
    return () => container.removeEventListener('mousemove', handleMousePos);
  }, []);

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <div className="relative z-10">{children}</div>
      <motion.div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: `radial-gradient(${radius}px circle at ${mousePos.x}px ${mousePos.y}px, rgba(6, 182, 212, ${intensity}) 0%, transparent 70%)`,
        }}
        animate={{ opacity: [0, 1] }}
        transition={{ duration: 0.3 }}
      />
    </div>
  );
}

SpotlightGrid.Card = function SpotlightCard({ children, className = '', ...props }) {
  return (
    <div
      className={`relative overflow-hidden rounded-2xl bg-slate-900/60 backdrop-blur border border-slate-800/80 hover:border-cyan-500/50 transition-all duration-300 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};
