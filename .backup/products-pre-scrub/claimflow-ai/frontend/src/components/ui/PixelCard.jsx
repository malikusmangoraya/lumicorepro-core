import React from 'react';
import { cn } from '../../utils';

const PixelCard = React.forwardRef(
  ({ children, className = '', title, icon: Icon, corners = true, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'relative border-2 border-foreground/90 bg-card font-mono shadow-[6px_6px_0_0_rgba(0,0,0,0.75)]',
        'p-6 transition-transform duration-100 hover:-translate-x-[2px] hover:-translate-y-[2px] hover:shadow-[8px_8px_0_0_rgba(0,0,0,0.75)]',
        corners && '[--px:7px]',
        className
      )}
      {...props}
    >
      {corners && (
        <>
          <span className="pointer-events-none absolute -left-1 -top-1 h-1 w-1 bg-foreground/90" />
          <span className="pointer-events-none absolute -right-1 -top-1 h-1 w-1 bg-foreground/90" />
          <span className="pointer-events-none absolute -bottom-1 -left-1 h-1 w-1 bg-foreground/90" />
          <span className="pointer-events-none absolute -bottom-1 -right-1 h-1 w-1 bg-foreground/90" />
        </>
      )}
      {(title || Icon) && (
        <div className="mb-4 flex items-center gap-2">
          {Icon && <Icon className="h-4 w-4 shrink-0 text-primary" />}
          {title && <h3 className="text-sm font-bold uppercase tracking-wider">{title}</h3>}
        </div>
      )}
      {children}
    </div>
  )
);

PixelCard.displayName = 'PixelCard';

export default PixelCard;
