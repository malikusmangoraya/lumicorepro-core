import React, { useRef, useEffect, useState } from 'react';
import { motion } from 'framer-motion';

const ScrollReveal = React.forwardRef(
  (
    {
      children,
      className = '',
      animate = 'fade-up',
      delay = 0,
      duration = 0.6,
      once = true,
      threshold = 0.1,
      rootMargin = '0px',
      ...props
    },
    ref
  ) => {
    const elementRef = useRef(null);
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
      const element = elementRef.current;
      if (!element) return;

      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) {
            setIsVisible(true);
            if (once) {
              observer.unobserve(element);
            }
          } else if (!once) {
            setIsVisible(false);
          }
        },
        { threshold, rootMargin }
      );

      observer.observe(element);
      return () => observer.disconnect();
    }, [once, threshold, rootMargin]);

    const animations = {
      'fade-up': { opacity: [0, 1], y: [30, 0] },
      'fade-down': { opacity: [0, 1], y: [-30, 0] },
      'fade-left': { opacity: [0, 1], x: [30, 0] },
      'fade-right': { opacity: [0, 1], x: [-30, 0] },
      'scale-up': { opacity: [0, 1], scale: [0.9, 1] },
      'scale-down': { opacity: [0, 1], scale: [1.1, 1] },
      'flip-up': { opacity: [0, 1], rotateX: [90, 0] },
      'slide-up': { opacity: [0, 1], y: [50, 0] },
      'slide-down': { opacity: [0, 1], y: [-50, 0] },
    };

    const animation = animations[animate] || animations['fade-up'];

    return (
      <motion.div
        ref={(el) => {
          elementRef.current = el;
          if (typeof ref === 'function') ref(el);
          else if (ref) ref.current = el;
        }}
        className={className}
        initial={false}
        animate={isVisible ? animation : { opacity: 0 }}
        transition={{
          duration,
          delay,
          ease: [0.22, 1, 0.36, 1],
        }}
        {...props}
      >
        {children}
      </motion.div>
    );
  }
);

ScrollReveal.displayName = 'ScrollReveal';

export default ScrollReveal;