import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { VehicleForm, type VehicleFormValues } from '@/components/admin/vehicle-form';
import { prisma } from '@/lib/prisma';
import { parseJson } from '@/lib/utils';

export const dynamic = 'force-dynamic';
export const metadata: Metadata = { title: 'Edit vehicle', robots: { index: false } };

export default async function EditVehiclePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  let vehicle;
  try {
    vehicle = await prisma.vehicle.findUnique({ where: { slug } });
  } catch {
    vehicle = null;
  }
  if (!vehicle) notFound();

  const initial: VehicleFormValues = {
    make: vehicle.make,
    model: vehicle.model,
    year: vehicle.year,
    title: vehicle.title,
    description: vehicle.description,
    price: vehicle.price,
    currency: vehicle.currency,
    mileage: vehicle.mileage,
    mileageUnit: vehicle.mileageUnit,
    bodyStyle: vehicle.bodyStyle,
    fuelType: vehicle.fuelType,
    transmission: vehicle.transmission,
    locationCountry: vehicle.locationCountry,
    locationRegion: vehicle.locationRegion,
    status: vehicle.status,
    isFeatured: vehicle.isFeatured,
    media: parseJson<{ url: string; alt: string }[]>(vehicle.media, []),
    inspectionReferences: parseJson<string[]>(vehicle.inspectionReferences, []),
    provenanceVerified: vehicle.provenanceVerified,
    conditionNotes: vehicle.conditionNotes,
    conditionReportUrl: vehicle.conditionReportUrl,
    vin: vehicle.vin,
  };

  return (
    <div className="space-y-5">
      <div>
        <Link
          href="/admin/vehicles"
          className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-heading"
        >
          <ArrowLeft className="size-4" aria-hidden="true" />
          Back to vehicles
        </Link>
        <h2 className="mt-3 font-display text-xl font-700 text-heading">{vehicle.title}</h2>
        <p className="mt-1 text-sm text-muted">
          Slug <code className="rounded bg-canvas px-1.5 py-0.5 text-xs">{vehicle.slug}</code> ·
          editing the public listing.
        </p>
      </div>
      <VehicleForm mode="edit" slug={vehicle.slug} initial={initial} />
    </div>
  );
}
