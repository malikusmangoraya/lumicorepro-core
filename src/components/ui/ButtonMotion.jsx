import React from 'react';
import { motion } from 'framer-motion';
import Button from './Button';
import { cn } from '../../utils';

const ButtonMotion = React.forwardRef(
  (
    { children, className = '', hoverScale = 1.02, tapScale = 0.96, hoverY = -1, ...props },
    ref
  ) => {
    return (
      <motion.div
        whileHover={{ scale: hoverScale, y: hoverY }}
        whileTap={{ scale: tapScale }}
        transition={{ type: 'spring', stiffness: 400, damping: 20 }}
        className={cn('inline-flex', className)}
      >
        <Button ref={ref} {...props}>
          {children}
        </Button>
      </motion.div>
    );
  }
);

ButtonMotion.displayName = 'ButtonMotion';

export default ButtonMotion;
