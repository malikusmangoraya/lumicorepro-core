import type { Metadata } from 'next';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { VehicleForm } from '@/components/admin/vehicle-form';

export const metadata: Metadata = { title: 'New vehicle', robots: { index: false } };

export default function NewVehiclePage() {
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
        <h2 className="mt-3 font-display text-xl font-700 text-heading">New vehicle</h2>
        <p className="mt-1 text-sm text-muted">
          Saved as a draft unless you set the status to active. The slug is generated from the year,
          make and model.
        </p>
      </div>
      <VehicleForm mode="create" />
    </div>
  );
}
