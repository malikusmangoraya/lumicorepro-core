import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import LazyImage from '../common/LazyImage';

function formatPrice(amount, currency) {
  try {
    return new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(Number(amount));
  } catch {
    return `${amount} ${currency}`;
  }
}

export default function VehicleCard({ vehicle }) {
  const image = Array.isArray(vehicle.media) ? vehicle.media[0] : null;
  const imageUrl = typeof image === 'string' ? image : image?.url;
  const mileage = vehicle.mileage == null ? null : `${Number(vehicle.mileage).toLocaleString()} ${vehicle.mileage_unit || 'km'}`;
  const specs = [vehicle.year, vehicle.body_style, mileage].filter(Boolean);

  return (
    <article className="overflow-hidden border border-[var(--t-border)] bg-surface">
      {imageUrl ? (
        <LazyImage src={imageUrl} alt={`${vehicle.title} vehicle`} ratio="16 / 10" />
      ) : (
        <div className="flex aspect-[16/10] items-center justify-center bg-slate-100 text-sm text-slate-500" role="img" aria-label="No vehicle image available">
          Image not available
        </div>
      )}
      <div className="p-5">
        {(vehicle.location_region || vehicle.location_country) && (
          <p className="text-xs uppercase tracking-widest text-slate-500">
            {[vehicle.location_region, vehicle.location_country].filter(Boolean).join(', ')}
          </p>
        )}
        <h2 className="mt-2 text-xl font-bold text-[var(--t-heading)]">{vehicle.title}</h2>
        {specs.length > 0 && <p className="mt-2 text-sm text-slate-500">{specs.join(' · ')}</p>}
        {vehicle.price != null && vehicle.currency && (
          <p className="mt-4 font-semibold">{formatPrice(vehicle.price, vehicle.currency)}</p>
        )}
        <Link to={`/inventory/${encodeURIComponent(vehicle.slug)}`} className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[var(--t-primary)]">
          View vehicle <ArrowRight className="h-4 w-4" aria-hidden="true" />
        </Link>
      </div>
    </article>
  );
}
