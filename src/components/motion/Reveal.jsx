import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../utils';

const directionMap = {
  up: { y: 32, x: 0 },
  down: { y: -32, x: 0 },
  left: { x: 32, y: 0 },
  right: { x: -32, y: 0 },
  none: { x: 0, y: 0 },
};

const Reveal = ({
  children,
  delay = 0,
  direction = 'up',
  className = '',
  as: Tag = 'div',
  ...props
}) => {
  const offset = directionMap[direction] || directionMap.up;

  return (
    <motion.div
      as={Tag}
      initial={{ opacity: 0, ...offset }}
      whileInView={{ opacity: 1, x: 0, y: 0 }}
      viewport={{ once: true, margin: '-40px' }}
      transition={{
        duration: 0.5,
        delay,
        ease: [0.22, 1, 0.36, 1],
      }}
      className={cn(className)}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export default Reveal;
