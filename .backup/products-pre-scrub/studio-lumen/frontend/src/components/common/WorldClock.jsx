import React, { useEffect, useState } from 'react';
import { Clock } from 'lucide-react';
import { cn } from '../../utils';

const DEFAULT_ZONES = [
  { city: 'New York', zone: 'America/New_York' },
  { city: 'London', zone: 'Europe/London' },
  { city: 'Dubai', zone: 'Asia/Dubai' },
  { city: 'Singapore', zone: 'Asia/Singapore' },
];

const timeIn = (zone) => {
  try {
    return new Intl.DateTimeFormat('en', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
      timeZone: zone,
    }).format(new Date());
  } catch (e) {
    return '--:--';
  }
};

const WorldClock = ({ zones = DEFAULT_ZONES, title = 'World clock', className = '' }) => {
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <aside
      className={cn('rounded-2xl border bg-card p-6 text-card-foreground shadow-sm', className)}
      aria-label={title}
    >
      <div className="flex items-center gap-2">
        <Clock className="h-4 w-4 text-primary" aria-hidden="true" />
        <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
          {title}
        </h3>
      </div>
      <ul className="mt-4 space-y-3">
        {zones.map(({ city, zone }) => (
          <li key={zone} className="flex items-center justify-between text-sm">
            <span className="font-medium text-foreground">{city}</span>
            <time className="tabular-nums text-muted-foreground">{timeIn(zone)}</time>
          </li>
        ))}
      </ul>
    </aside>
  );
};

export default WorldClock;
