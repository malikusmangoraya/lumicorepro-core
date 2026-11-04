import Image from 'next/image';
import Link from 'next/link';
import { Gauge, MapPin, ShieldCheck } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { SaveButton } from '@/components/vehicle/save-button';
import { CompareButton } from '@/components/vehicle/compare-button';
import { formatCurrency, formatMileage } from '@/lib/utils';
import type { VehicleCardData } from '@/lib/vehicles';

export function VehicleCard({ vehicle }: { vehicle: VehicleCardData }) {
  const cover = vehicle.media[0];

  return (
    <article className="group relative overflow-hidden rounded-panel border border-line bg-surface/70 transition-colors hover:border-primary/50">
      {/* Actions sit outside the Link: a button nested inside an anchor is
          invalid HTML and swallows the click on touch devices. */}
      <div className="absolute right-3 top-3 z-10 flex flex-col gap-2">
        <SaveButton slug={vehicle.slug} title={vehicle.title} />
        <CompareButton slug={vehicle.slug} title={vehicle.title} />
      </div>

      <Link href={`/inventory/${vehicle.slug}`} className="block focus-visible:outline-none">
        <div className="relative aspect-[16/10] overflow-hidden bg-canvas">
          {cover ? (
            <Image
              src={cover.url}
              alt={cover.alt || vehicle.title}
              fill
              sizes="(max-width: 768px) 100vw, 33vw"
              className="object-cover transition-transform duration-500 group-hover:scale-[1.03]"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-muted">
              No image
            </div>
          )}
          <div className="absolute left-3 top-3 flex gap-2">
            <Badge tone="neutral">{vehicle.year}</Badge>
            {vehicle.provenanceVerified && (
              <Badge tone="success">
                <ShieldCheck className="size-3" aria-hidden="true" />
                Provenance
              </Badge>
            )}
          </div>
        </div>

        <div className="space-y-3 p-5">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="font-display text-lg font-600 leading-snug text-heading">
                {vehicle.title}
              </h3>
              <p className="mt-1 text-sm text-muted">
                {vehicle.make} {vehicle.model} · {vehicle.bodyStyle}
              </p>
            </div>
            <p className="shrink-0 font-display text-lg font-700 text-accent">
              {formatCurrency(vehicle.price, vehicle.currency)}
            </p>
          </div>

          <dl className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-muted">
            <div className="flex items-center gap-1.5">
              <Gauge className="size-3.5" aria-hidden="true" />
              <dt className="sr-only">Mileage</dt>
              <dd>{formatMileage(vehicle.mileage, vehicle.mileageUnit)}</dd>
            </div>
            <div className="flex items-center gap-1.5">
              <MapPin className="size-3.5" aria-hidden="true" />
              <dt className="sr-only">Location</dt>
              <dd>
                {vehicle.locationRegion}, {vehicle.locationCountry}
              </dd>
            </div>
            <div>
              <dt className="sr-only">Transmission</dt>
              <dd>{vehicle.transmission}</dd>
            </div>
          </dl>
        </div>
      </Link>
    </article>
  );
}
