import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../utils';

const Collapsible = React.forwardRef(
  (
    {
      children,
      open = false,
      onOpenChange,
      className = '',
      ...props
    },
    ref
  ) => {
    const [isOpen, setIsOpen] = useState(open);
    const contentRef = useRef(null);

    useEffect(() => {
      setIsOpen(open);
    }, [open]);

    const handleToggle = () => {
      const newState = !isOpen;
      setIsOpen(newState);
      onOpenChange?.(newState);
    };

    return (
      <div ref={ref} className={cn('w-full', className)} {...props}>
        {React.Children.map(children, child => {
          if (!React.isValidElement(child)) return child;
          
          if (child.type === CollapsibleTrigger) {
            return React.cloneElement(child, { onClick: handleToggle });
          }
          if (child.type === CollapsibleContent) {
            return React.cloneElement(child, { isOpen, contentRef });
          }
          return child;
        })}
      </div>
    );
  }
);

Collapsible.displayName = 'Collapsible';

const CollapsibleTrigger = React.forwardRef(
  ({ children, className = '', onClick, ...props }, ref) => (
    <button
      ref={ref}
      type="button"
      className={cn('w-full', className)}
      onClick={onClick}
      {...props}
    >
      {children}
    </button>
  )
);

CollapsibleTrigger.displayName = 'CollapsibleTrigger';

const CollapsibleContent = React.forwardRef(
  ({ children, isOpen = false, contentRef, className = '', ...props }, ref) => (
    <motion.div
      ref={(el) => {
        contentRef.current = el;
        if (typeof ref === 'function') ref(el);
        else if (ref) ref.current = el;
      }}
      className={cn('overflow-hidden', className)}
      initial={false}
      animate={{ height: isOpen ? 'auto' : 0, opacity: isOpen ? 1 : 0 }}
      transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
      style={{ overflow: 'hidden' }}
      {...props}
    >
      <div style={{ overflow: 'hidden' }}>{children}</div>
    </motion.div>
  )
);

CollapsibleContent.displayName = 'CollapsibleContent';

export { Collapsible, CollapsibleTrigger, CollapsibleContent };
export default Collapsible;