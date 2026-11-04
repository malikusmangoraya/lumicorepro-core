import Link from 'next/link';
import { Plus } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { ButtonLink } from '@/components/ui/button';
import { Panel } from '@/components/ui/card';
import { VehicleRowActions } from '@/components/admin/vehicle-row-actions';
import type { Prisma } from '@prisma/client';
import { prisma } from '@/lib/prisma';
import { formatCurrency, formatMileage, parseJson } from '@/lib/utils';

export const dynamic = 'force-dynamic';

const TONES: Record<string, 'primary' | 'success' | 'warning' | 'danger' | 'neutral'> = {
  active: 'success',
  draft: 'warning',
  reserved: 'primary',
  sold: 'neutral',
  withdrawn: 'danger',
};

export default async function AdminVehiclesPage() {
  let vehicles: Prisma.VehicleGetPayload<Record<string, never>>[] = [];
  let ready = true;

  try {
    vehicles = await prisma.vehicle.findMany({ orderBy: [{ updatedAt: 'desc' }] });
  } catch {
    ready = false;
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-display text-xl font-700 text-heading">Vehicles</h2>
          <p className="mt-1 text-sm text-muted">
            {vehicles.length} in the database. Withdrawing keeps the row so customer history
            survives.
          </p>
        </div>
        <ButtonLink href="/admin/vehicles/new">
          <Plus className="size-4" aria-hidden="true" />
          New vehicle
        </ButtonLink>
      </div>

      {!ready ? (
        <Panel className="p-6 text-sm text-muted">
          The database is not initialised. Run{' '}
          <code className="rounded bg-canvas px-1.5 py-0.5">npm run db:setup</code>.
        </Panel>
      ) : vehicles.length === 0 ? (
        <Panel className="p-10 text-center">
          <p className="font-600 text-heading">No vehicles yet</p>
          <p className="mx-auto mt-2 max-w-sm text-sm text-muted">
            Create the first listing, or run the seed to load six demo cars.
          </p>
          <div className="mt-5">
            <ButtonLink href="/admin/vehicles/new">Create a vehicle</ButtonLink>
          </div>
        </Panel>
      ) : (
        <Panel className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[860px] text-left text-sm">
              <thead className="text-xs uppercase tracking-wide text-muted">
                <tr className="border-b border-line/70">
                  <th scope="col" className="px-5 py-3 font-medium">Vehicle</th>
                  <th scope="col" className="px-5 py-3 font-medium">Status</th>
                  <th scope="col" className="px-5 py-3 font-medium">Price</th>
                  <th scope="col" className="px-5 py-3 font-medium">Mileage</th>
                  <th scope="col" className="px-5 py-3 font-medium">Photos</th>
                  <th scope="col" className="px-5 py-3 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line/50">
                {vehicles.map((vehicle) => {
                  const media = parseJson<unknown[]>(vehicle.media, []);
                  return (
                    <tr key={vehicle.id}>
                      <td className="px-5 py-3">
                        <Link
                          href={`/inventory/${vehicle.slug}`}
                          className="font-medium text-heading hover:text-accent"
                        >
                          {vehicle.title}
                        </Link>
                        <p className="text-xs text-muted">
                          {vehicle.make} {vehicle.model} · {vehicle.year}
                          {vehicle.isFeatured && ' · featured'}
                        </p>
                      </td>
                      <td className="px-5 py-3">
                        <Badge tone={TONES[vehicle.status] ?? 'neutral'}>{vehicle.status}</Badge>
                      </td>
                      <td className="px-5 py-3 text-heading">
                        {formatCurrency(vehicle.price, vehicle.currency)}
                      </td>
                      <td className="px-5 py-3 text-muted">
                        {formatMileage(vehicle.mileage, vehicle.mileageUnit)}
                      </td>
                      <td className="px-5 py-3 text-muted">{media.length}</td>
                      <td className="px-5 py-3">
                        <VehicleRowActions
                          slug={vehicle.slug}
                          title={vehicle.title}
                          status={vehicle.status}
                        />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Panel>
      )}
    </div>
  );
}
