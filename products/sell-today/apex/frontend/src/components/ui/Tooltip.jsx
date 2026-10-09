import React, { useState, useRef, useEffect } from 'react';
import { cn } from '../../utils';

/**
 * Tooltip primitive.
 *
 * Deliberately CSS-animated rather than framer-motion animated: this component is
 * statically reachable from the first-paint path (MainLayout -> GlassNavbar ->
 * IconButton -> Tooltip), so importing framer-motion here forced ~35 KB gzip of
 * animation runtime onto the critical path for a fade. The bundle budget gate
 * (`npm run size`) fails if that regresses.
 *
 * The outer div owns placement (so the enter/exit offset below can never fight
 * the centring translate in `positions`), the inner div owns the transform.
 */

const positions = {
  top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
  bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
  left: 'right-full top-1/2 -translate-y-1/2 mr-2',
  right: 'left-full top-1/2 -translate-y-1/2 ml-2',
};

const EXIT_MS = 150;

const Tooltip = ({
  children,
  content,
  position = 'top',
  delay = 200,
  open: controlledOpen,
  onOpenChange,
  className = '',
}) => {
  const [open, setOpen] = useState(false);
  const [entered, setEntered] = useState(false);
  const openTimer = useRef(null);
  const closeTimer = useRef(null);
  const isControlled = controlledOpen !== undefined;
  const isOpen = isControlled ? controlledOpen : open;

  useEffect(() => {
    return () => {
      if (openTimer.current) clearTimeout(openTimer.current);
      if (closeTimer.current) clearTimeout(closeTimer.current);
    };
  }, []);

  // In controlled mode the parent owns visibility, and it can flip `open` at any
  // time (or start out true) without going through show/hide. Mirror it into
  // `entered` or the fade never runs and the tooltip stays at opacity-0.
  useEffect(() => {
    if (isControlled) setEntered(controlledOpen);
  }, [isControlled, controlledOpen]);

  // In controlled mode the parent owns visibility, and it can flip `open` at any
  // time (or start out true) without going through show/hide. Mirror it into
  // `entered` or the fade never runs and the tooltip stays at opacity-0.
  const show = () => {
    // A pending unmount from a fast re-hover must not fire.
    if (closeTimer.current) {
      clearTimeout(closeTimer.current);
      closeTimer.current = null;
    }
    if (isControlled) {
      onOpenChange?.(true);
      return;
    }
    if (openTimer.current) clearTimeout(openTimer.current);
    openTimer.current = setTimeout(() => {
      setOpen(true);
      onOpenChange?.(true);
      requestAnimationFrame(() => setEntered(true));
    }, delay);
  };

  const hide = () => {
    if (openTimer.current) {
      clearTimeout(openTimer.current);
      openTimer.current = null;
    }
    setEntered(false);
    onOpenChange?.(false);
    if (isControlled) return;
    // Keep mounted through the exit transition, then drop it.
    if (closeTimer.current) clearTimeout(closeTimer.current);
    closeTimer.current = setTimeout(() => setOpen(false), EXIT_MS);
  };

  return (
    <div
      className="relative inline-flex"
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
    >
      {children}
      {isOpen && (
        <div
          role="tooltip"
          className={cn(
            'absolute z-50 px-2.5 py-1.5 text-xs font-medium text-white bg-gray-900',
            'dark:bg-gray-100 dark:text-gray-900 rounded-lg shadow-lg whitespace-nowrap',
            positions[position],
            className
          )}
        >
          <div
            className={cn(
              'transition-[opacity,transform] duration-150 ease-out motion-reduce:transition-none',
              entered ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-1'
            )}
          >
            {content}
          </div>
        </div>
      )}
    </div>
  );
};

export default Tooltip;
