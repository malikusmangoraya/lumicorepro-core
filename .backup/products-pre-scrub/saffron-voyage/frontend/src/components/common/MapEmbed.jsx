import React from 'react';
import { MapPin } from 'lucide-react';
import { cn } from '../../utils';

const MapEmbed = ({
  query = 'Downtown New York',
  title = 'Our location',
  height = 'h-80',
  zoom = 14,
  className = '',
}) => {
  const src = `https://maps.google.com/maps?q=${encodeURIComponent(query)}&z=${zoom}&output=embed`;

  return (
    <div
      className={cn(
        'relative w-full overflow-hidden rounded-2xl border bg-muted',
        height,
        className
      )}
    >
      <iframe
        src={src}
        title={title}
        loading="lazy"
        referrerPolicy="no-referrer-when-downgrade"
        allowFullScreen
        className="h-full w-full border-0"
        style={{ filter: 'invert(0.85) hue-rotate(180deg) contrast(0.9)' }}
      />
      <span className="pointer-events-none absolute left-3 top-3 inline-flex items-center gap-1.5 rounded-full bg-background/90 px-2.5 py-1 text-xs font-medium shadow-sm backdrop-blur">
        <MapPin className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
        {query}
      </span>
    </div>
  );
};

export default MapEmbed;
