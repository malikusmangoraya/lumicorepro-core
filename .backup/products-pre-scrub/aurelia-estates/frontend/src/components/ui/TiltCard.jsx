import React, { useCallback } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { cn } from '../../utils';

const TiltCard = React.forwardRef(
  ({ children, className = '', tilt = 10, shadow = true, scale = 1.02, ...props }, ref) => {
    const x = useMotionValue(0);
    const y = useMotionValue(0);
    const rotateX = useSpring(useTransform(y, [-0.5, 0.5], [tilt, -tilt]), {
      stiffness: 180,
      damping: 16,
    });
    const rotateY = useSpring(useTransform(x, [-0.5, 0.5], [-tilt, tilt]), {
      stiffness: 180,
      damping: 16,
    });

    const handleMove = useCallback(
      (e) => {
        const el = e.currentTarget;
        const rect = el.getBoundingClientRect();
        x.set((e.clientX - rect.left) / rect.width - 0.5);
        y.set((e.clientY - rect.top) / rect.height - 0.5);
      },
      [x, y]
    );

    const handleLeave = useCallback(() => {
      x.set(0);
      y.set(0);
    }, [x, y]);

    return (
      <div className="[perspective:1000px]">
        <motion.div
          ref={ref}
          onMouseMove={handleMove}
          onMouseLeave={handleLeave}
          style={{ rotateX, rotateY, transformStyle: 'preserve-3d' }}
          whileHover={{ scale }}
          className={cn('relative rounded-xl bg-card', shadow && 'shadow-lg', className)}
          {...props}
        >
          {children}
        </motion.div>
      </div>
    );
  }
);

TiltCard.displayName = 'TiltCard';

export default TiltCard;
