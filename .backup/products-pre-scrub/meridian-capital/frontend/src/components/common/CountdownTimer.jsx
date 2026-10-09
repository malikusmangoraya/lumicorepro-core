import React, { useEffect, useState } from 'react';
import { cn } from '../../utils';

const pad = (n) => String(n).padStart(2, '0');

const timeLeft = (target) => {
  const diff = Math.max(0, new Date(target).getTime() - Date.now());
  return {
    days: Math.floor(diff / 86400000),
    hours: Math.floor((diff / 3600000) % 24),
    minutes: Math.floor((diff / 60000) % 60),
    seconds: Math.floor((diff / 1000) % 60),
  };
};

const CountdownTimer = ({
  target,
  title = 'Offer ends in',
  onComplete,
  labels = { days: 'Days', hours: 'Hours', minutes: 'Minutes', seconds: 'Seconds' },
  variant = 'blanks',
  className = '',
}) => {
  const [left, setLeft] = useState(() => timeLeft(target));

  useEffect(() => {
    const id = setInterval(() => {
      const next = timeLeft(target);
      setLeft(next);
      if (next.days + next.hours + next.minutes + next.seconds <= 0) {
        clearInterval(id);
        if (typeof onComplete === 'function') onComplete();
      }
    }, 1000);
    return () => clearInterval(id);
  }, [target, onComplete]);

  const units = [
    { key: 'days', value: left.days },
    { key: 'hours', value: left.hours },
    { key: 'minutes', value: left.minutes },
    { key: 'seconds', value: left.seconds },
  ];

  return (
    <div className={cn('space-y-3', className)}>
      {title && (
        <p className="text-sm font-medium uppercase tracking-wider text-muted-foreground">
          {title}
        </p>
      )}
      <div className="flex items-center gap-2" role="timer" aria-label={title}>
        {units.map(({ key, value }) => (
          <div key={key} className="flex items-center gap-2">
            <div
              className={cn(
                'flex h-14 w-14 flex-col items-center justify-center rounded-lg border text-center',
                variant === 'solid'
                  ? 'border-transparent bg-primary text-primary-foreground'
                  : 'bg-card'
              )}
            >
              <span className="text-xl font-bold tabular-nums">{pad(value)}</span>
              <span
                className={cn(
                  'text-[10px] uppercase tracking-wide',
                  variant === 'solid' ? 'text-primary-foreground/80' : 'text-muted-foreground'
                )}
              >
                {labels[key]}
              </span>
            </div>
            {key !== 'seconds' && (
              <span className="font-bold text-muted-foreground" aria-hidden="true">
                :
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default CountdownTimer;
