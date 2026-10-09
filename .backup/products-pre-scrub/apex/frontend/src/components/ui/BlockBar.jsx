import React from 'react';
import { cn } from '../../utils';

const BlockBar = ({
  value = 0,
  max = 100,
  segments = 10,
  tone = 'primary',
  label = '',
  showValue = true,
  className = '',
  inverted = false,
}) => {
  const safeMax = Math.max(1, Number(max) || 1);
  const pct = Math.min(1, Math.max(0, Number(value) / safeMax));
  const filled = Math.round(pct * segments);

  return (
    <div className={cn('space-y-1.5', className)}>
      {(label || showValue) && (
        <div className="flex items-center justify-between font-mono text-xs text-muted-foreground">
          <span>{label}</span>
          {showValue && (
            <span className="tabular-nums">
              {value}/{max}
            </span>
          )}
        </div>
      )}
      <div
        role="progressbar"
        aria-valuenow={Math.round(Number(value) || 0)}
        aria-valuemin={0}
        aria-valuemax={Math.round(safeMax)}
        className="flex gap-[3px]"
      >
        {Array.from({ length: segments }).map((_, i) => {
          const on = inverted ? i >= segments - filled : i < filled;
          return (
            <span
              key={i}
              className={cn(
                'h-3 flex-1 border border-foreground/50 transition-colors',
                on ? (tone === 'primary' ? 'bg-primary' : 'bg-accent') : 'bg-muted opacity-50'
              )}
            />
          );
        })}
      </div>
    </div>
  );
};

BlockBar.displayName = 'BlockBar';

export default BlockBar;
