import React, { useRef, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/utils';

export function MagneticButton({
  children,
  className = '',
  strength = 30, // magnetic pull radius/force
  onClick,
  variant = 'primary', // 'primary' | 'glow' | 'outline' | 'ghost'
  size = 'md', // 'sm' | 'md' | 'lg'
  leftIcon: LeftIcon,
  rightIcon: RightIcon,
  ...props
}) {
  const buttonRef = useRef(null);
  const [position, setPosition] = useState({ x: 0, y: 0 });

  const handleMouseMove = useCallback(
    (e) => {
      if (!buttonRef.current) return;
      const { clientX, clientY } = e;
      const { left, top, width, height } = buttonRef.current.getBoundingClientRect();
      const middleX = clientX - (left + width / 2);
      const middleY = clientY - (top + height / 2);
      setPosition({
        x: (middleX / width) * strength,
        y: (middleY / height) * strength,
      });
    },
    [strength]
  );

  const handleMouseLeave = useCallback(() => {
    setPosition({ x: 0, y: 0 });
  }, []);

  const sizeClasses = {
    sm: 'px-3.5 py-1.5 text-xs',
    md: 'px-5 py-2.5 text-sm',
    lg: 'px-7 py-3.5 text-base',
  }[size] || 'px-5 py-2.5 text-sm';

  const variantClasses = {
    primary:
      'bg-primary text-primary-foreground shadow-lg shadow-primary/25 hover:bg-primary/90 hover:shadow-primary/40',
    glow:
      'relative bg-gradient-to-r from-cyan-500 to-violet-600 text-white shadow-lg shadow-cyan-500/30 hover:shadow-cyan-500/50 hover:scale-[1.02]',
    outline:
      'border border-border/80 bg-background/80 backdrop-blur-sm text-foreground hover:border-primary hover:bg-primary/10',
    ghost: 'text-foreground hover:bg-accent/50',
  }[variant] || 'bg-primary text-primary-foreground';

  return (
    <motion.button
      ref={buttonRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      animate={{ x: position.x, y: position.y }}
      transition={{ type: 'spring', stiffness: 350, damping: 20, mass: 0.5 }}
      onClick={onClick}
      className={cn(
        'group relative inline-flex items-center justify-center gap-2 rounded-xl font-medium tracking-tight select-none transition-all duration-200 active:scale-95 disabled:pointer-events-none disabled:opacity-50',
        sizeClasses,
        variantClasses,
        className
      )}
      {...props}
    >
      {LeftIcon && <LeftIcon className="h-4 w-4 shrink-0 transition-transform group-hover:-translate-x-0.5" />}
      <span className="relative z-10">{children}</span>
      {RightIcon && <RightIcon className="h-4 w-4 shrink-0 transition-transform group-hover:translate-x-0.5" />}
    </motion.button>
  );
}

export default MagneticButton;
