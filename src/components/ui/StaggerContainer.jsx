import React from 'react';
import { motion } from 'framer-motion';

const staggerContainer = {
  hidden: {},
  show: {
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1,
    },
  },
};

const staggerItem = {
  hidden: { opacity: 0, y: 20 },
  show: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      ease: [0.22, 1, 0.36, 1],
    },
  },
};

const StaggerContainer = React.forwardRef(
  (
    {
      children,
      className = '',
      animate = 'show',
      initial = 'hidden',
      stagger = 0.1,
      delayChildren = 0.1,
      direction = 'vertical',
      ...props
    },
    ref
  ) => {
    const containerVariants = {
      hidden: {},
      show: {
        transition: {
          staggerChildren: stagger,
          delayChildren,
        },
      },
    };

    const itemVariants = {
      hidden: direction === 'horizontal' ? { opacity: 0, x: 20 } : { opacity: 0, y: 20 },
      show: {
        opacity: 1,
        x: 0,
        y: 0,
        transition: {
          duration: 0.5,
          ease: [0.22, 1, 0.36, 1],
        },
      },
    };

    return (
      <motion.div
        ref={ref}
        className={className}
        variants={containerVariants}
        initial={initial}
        animate={animate}
        {...props}
      >
        {React.Children.map(children, (child, index) =>
          React.isValidElement(child) ? (
            React.cloneElement(child, {
              variants: itemVariants,
              style: { ...child.props.style, transitionDelay: index * stagger * 1000 },
            })
          ) : child
        )}
      </motion.div>
    );
  }
);

StaggerContainer.displayName = 'StaggerContainer';

export { staggerContainer, staggerItem };
export default StaggerContainer;