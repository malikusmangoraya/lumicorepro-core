/**
 * GlassCard - Premium Glassmorphism Component
 * ============================================
 * A beautiful card with frosted glass effect, gradient borders, and smooth animations.
 * 
 * Features:
 * - Backdrop blur effect
 * - Gradient border animations
 * - Hover 3D tilt effect
 * - Customizable glass intensity
 * - Dark/light mode support
 */

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import PropTypes from 'prop-types';

const GlassCard = ({
  children,
  className = '',
  intensity = 'medium',
  gradient = true,
  tiltEffect = true,
  onClick,
  hoverable = true,
  borderRadius = 'xl',
  ...props
}) => {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = (e) => {
    if (!tiltEffect) return;
    
    const card = e.currentTarget;
    const rect = card.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;
    
    setMousePosition({ x, y });
  };

  const handleMouseLeave = () => {
    setIsHovered(false);
    setMousePosition({ x: 0.5, y: 0.5 });
  };

  // Glass intensity presets
  const intensityClasses = {
    low: 'backdrop-blur-sm bg-white/5 dark:bg-white/5',
    medium: 'backdrop-blur-md bg-white/10 dark:bg-white/10',
    high: 'backdrop-blur-lg bg-white/20 dark:bg-white/20',
    ultra: 'backdrop-blur-xl bg-white/30 dark:bg-white/30',
  };

  const borderRadiusClasses = {
    none: 'rounded-none',
    sm: 'rounded-sm',
    md: 'rounded-md',
    lg: 'rounded-lg',
    xl: 'rounded-xl',
    '2xl': 'rounded-2xl',
    '3xl': 'rounded-3xl',
    full: 'rounded-full',
  };

  // Calculate tilt transform
  const tiltTransform = tiltEffect && isHovered
    ? {
        rotateX: (mousePosition.y - 0.5) * 10,
        rotateY: (mousePosition.x - 0.5) * -10,
        scale: 1.02,
      }
    : {
        rotateX: 0,
        rotateY: 0,
        scale: 1,
      };

  return (
    <motion.div
      className={`
        glass-card
        ${intensityClasses[intensity]}
        ${borderRadiusClasses[borderRadius]}
        ${gradient ? 'glass-gradient-border' : 'border border-white/20 dark:border-white/20'}
        ${hoverable ? 'hover:shadow-2xl hover:shadow-primary/20 transition-shadow duration-300' : ''}
        ${onClick ? 'cursor-pointer' : ''}
        ${className}
        relative overflow-hidden
        shadow-lg
        p-6
      `}
      style={{
        perspective: '1000px',
        transformStyle: 'preserve-3d',
      }}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      animate={tiltTransform}
      transition={{
        type: 'spring',
        stiffness: 300,
        damping: 20,
      }}
      {...props}
    >
      {/* Gradient border animation */}
      {gradient && (
        <motion.div
          className="absolute inset-0 rounded-[inherit] p-[1px] bg-gradient-to-br from-primary/50 via-secondary/50 to-accent/50"
          style={{
            maskImage: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
            maskComposite: 'exclude',
            WebkitMaskComposite: 'xor',
          }}
          animate={{
            background: isHovered
              ? 'linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 50%, var(--color-accent) 100%)'
              : 'linear-gradient(135deg, rgba(var(--color-primary-rgb), 0.5) 0%, rgba(var(--color-secondary-rgb), 0.5) 50%, rgba(var(--color-accent-rgb), 0.5) 100%)',
          }}
          transition={{ duration: 0.3 }}
        />
      )}

      {/* Spotlight effect on hover */}
      {hoverable && (
        <motion.div
          className="absolute inset-0 opacity-0 pointer-events-none"
          style={{
            background: `radial-gradient(circle at ${mousePosition.x * 100}% ${mousePosition.y * 100}%, rgba(255,255,255,0.1) 0%, transparent 50%)`,
          }}
          animate={{
            opacity: isHovered ? 1 : 0,
          }}
          transition={{ duration: 0.2 }}
        />
      )}

      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>

      {/* Glass shimmer effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/0 via-white/5 to-white/0 pointer-events-none" />
    </motion.div>
  );
};

GlassCard.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
  intensity: PropTypes.oneOf(['low', 'medium', 'high', 'ultra']),
  gradient: PropTypes.bool,
  tiltEffect: PropTypes.bool,
  onClick: PropTypes.func,
  hoverable: PropTypes.bool,
  borderRadius: PropTypes.oneOf(['none', 'sm', 'md', 'lg', 'xl', '2xl', '3xl', 'full']),
};

export default GlassCard;
