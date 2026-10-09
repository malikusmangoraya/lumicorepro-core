import React, { useRef, useEffect, useState } from 'react';
import { motion } from 'framer-motion';

const Parallax = React.forwardRef(
  (
    {
      children,
      className = '',
      speed = 0.5,
      direction = 'vertical',
      wrapperClassName = '',
      ...props
    },
    ref
  ) => {
    const elementRef = useRef(null);
    const [offset, setOffset] = useState(0);

    useEffect(() => {
      const element = elementRef.current;
      if (!element) return;

      const handleScroll = () => {
        const rect = element.getBoundingClientRect();
        const viewportHeight = window.innerHeight;
        
        if (rect.bottom < 0 || rect.top > viewportHeight) return;
        
        const progress = (viewportHeight - rect.top) / (viewportHeight + rect.height);
        const clampedProgress = Math.max(0, Math.min(1, progress));
        setOffset(clampedProgress);
      };

      window.addEventListener('scroll', handleScroll, { passive: true });
      handleScroll();
      
      return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const transform = direction === 'vertical' 
      ? `translateY(${offset * speed * 100}px)`
      : `translateX(${offset * speed * 100}px)`;

    return (
      <div
        ref={ref}
        className={className}
        style={{
          overflow: 'hidden',
          position: 'relative',
          ...props.style,
        }}
        {...props}
      >
        <motion.div
          ref={elementRef}
          className={wrapperClassName}
          style={{
            transform,
            willChange: 'transform',
            width: '100%',
            height: '100%',
          }}
        >
          {children}
        </motion.div>
      </div>
    );
  }
);

Parallax.displayName = 'Parallax';

export default Parallax;