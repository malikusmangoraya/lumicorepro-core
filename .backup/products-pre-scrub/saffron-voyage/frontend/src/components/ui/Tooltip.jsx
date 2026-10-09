import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../utils';

const positions = {
  top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
  bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
  left: 'right-full top-1/2 -translate-y-1/2 mr-2',
  right: 'left-full top-1/2 -translate-y-1/2 ml-2',
};

const tooltipVariants = {
  hidden: { opacity: 0, y: 4 },
  visible: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 400, damping: 25 } },
  exit: { opacity: 0, y: 4, transition: { duration: 0.12 } },
};

const Tooltip = ({
  children,
  content,
  position = 'top',
  delay = 200,
  open: controlledOpen,
  onOpenChange,
  className = '',
}) => {
  const [visible, setVisible] = useState(false);
  const [show, setShow] = useState(false);
  const timeoutRef = useRef(null);
  const isControlled = controlledOpen !== undefined;
  const isOpen = isControlled ? controlledOpen : show;

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  const open = () => {
    setVisible(true);
    timeoutRef.current = setTimeout(() => {
      if (!isControlled) setShow(true);
      onOpenChange?.(true);
    }, delay);
  };

  const close = () => {
    setVisible(false);
    if (!isControlled) setShow(false);
    onOpenChange?.(false);
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
  };

  return (
    <div
      className="relative inline-flex"
      onMouseEnter={open}
      onMouseLeave={close}
      onFocus={open}
      onBlur={close}
    >
      {children}
      <AnimatePresence>
        {visible && isOpen && (
          <motion.div
            variants={tooltipVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            role="tooltip"
            className={cn(
              'absolute z-50 px-2.5 py-1.5 text-xs font-medium text-white bg-gray-900',
              'dark:bg-gray-100 dark:text-gray-900 rounded-lg shadow-lg whitespace-nowrap',
              positions[position],
              className
            )}
          >
            {content}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Tooltip;
