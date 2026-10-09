import React from 'react';
import Button from './Button';
import { cn } from '../../utils';

/**
 * Scale-on-hover/tap button wrapper.
 *
 * Was a framer-motion `motion.div`, but that put the whole ~35 KB gzip
 * framer-motion runtime on the first-paint path: ButtonMotion is reachable
 * statically from MainLayout -> GlassNavbar/ModernFooter -> Language, so
 * `npm run size` failed the initial-JS budget. Every one of its 28 call sites is
 * a hover/tap scale, which CSS transitions do for free, so the animation is
 * expressed as CSS custom properties instead.
 *
 * The API (`hoverScale`, `tapScale`, `hoverY`) and the className routing are
 * unchanged: `className` lands on the wrapper, everything else goes to `Button`,
 * and the ref still targets the inner `Button`.
 */
const ButtonMotion = React.forwardRef(
  (
    { children, className = '', hoverScale = 1.02, tapScale = 0.96, hoverY = -1, style, ...props },
    ref
  ) => {
    return (
      <div
        style={{
          '--bm-hover-scale': hoverScale,
          '--bm-tap-scale': tapScale,
          '--bm-hover-y': `${hoverY}px`,
          ...style,
        }}
        className={cn('bm-motion inline-flex', className)}
      >
        <Button ref={ref} {...props}>
          {children}
        </Button>
      </div>
    );
  }
);

ButtonMotion.displayName = 'ButtonMotion';

export default ButtonMotion;

export { ButtonMotion as ButtonMotion };
