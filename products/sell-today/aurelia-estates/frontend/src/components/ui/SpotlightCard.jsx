import React, { useCallback, useRef } from 'react';
import { cn } from '../../utils';

const SpotlightCard = React.forwardRef(
  (
    {
      children,
      className = '',
      interactive = true,
      spotlight = 'rgba(99,102,241,0.16)',
      radius = 600,
      onMouseMove,
      onMouseLeave,
      ...props
    },
    ref
  ) => {
    const surfaceRef = useRef(null);

    const handleMove = useCallback(
      (e) => {
        onMouseMove?.(e);
        if (!interactive) return;
        const el = surfaceRef.current;
        if (!el) return;
        const rect = el.getBoundingClientRect();
        el.style.setProperty('--spot-x', `${e.clientX - rect.left}px`);
        el.style.setProperty('--spot-y', `${e.clientY - rect.top}px`);
      },
      [interactive, onMouseMove]
    );

    const handleLeave = useCallback(
      (e) => {
        onMouseLeave?.(e);
        if (!interactive) return;
        const el = surfaceRef.current;
        if (el) {
          el.style.setProperty('--spot-x', '-100px');
          el.style.setProperty('--spot-y', '-100px');
        }
      },
      [interactive, onMouseLeave]
    );

    return (
      <div
        ref={(node) => {
          surfaceRef.current = node;
          if (typeof ref === 'function') ref(node);
          else if (ref) ref.current = node;
        }}
        onMouseMove={handleMove}
        onMouseLeave={handleLeave}
        className={cn(
          'group relative overflow-hidden rounded-xl border border-border bg-card',
          className
        )}
        {...props}
      >
        {interactive && (
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
            style={{
              background: `radial-gradient(${radius}px circle at var(--spot-x, -100px) var(--spot-y, -100px), ${spotlight}, transparent 40%)`,
            }}
          />
        )}
        {children}
      </div>
    );
  }
);

SpotlightCard.displayName = 'SpotlightCard';

export default SpotlightCard;
