'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Loader2, Save } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Field, Input, Select, Textarea } from '@/components/ui/field';
import { useSite } from '@/components/providers/site-provider';

export type VehicleFormValues = {
  make: string;
  model: string;
  year: number;
  title: string;
  description: string;
  price: number;
  currency: string;
  mileage: number;
  mileageUnit: string;
  bodyStyle: string;
  fuelType: string;
  transmission: string;
  locationCountry: string;
  locationRegion: string;
  status: string;
  isFeatured: boolean;
  media: { url: string; alt: string }[];
  inspectionReferences: string[];
  provenanceVerified: boolean;
  conditionNotes: string | null;
  conditionReportUrl: string | null;
  vin: string | null;
};

const CURRENCIES = ['USD', 'EUR', 'GBP', 'AED', 'PKR', 'INR'];
const STATUSES = ['draft', 'active', 'reserved', 'sold', 'withdrawn'];
const BODY_STYLES = ['Coupe', 'Convertible', 'Saloon', 'SUV', 'Estate', 'Hypercar'];
const FUELS = ['Petrol', 'Hybrid', 'Electric', 'Diesel'];
const TRANSMISSIONS = ['6-speed manual', '7-speed dual-clutch', '8-speed automatic'];

export const EMPTY_VEHICLE: VehicleFormValues = {
  make: '',
  model: '',
  year: new Date().getFullYear(),
  title: '',
  description: '',
  price: 0,
  currency: 'USD',
  mileage: 0,
  mileageUnit: 'mi',
  bodyStyle: 'Coupe',
  fuelType: 'Petrol',
  transmission: '6-speed manual',
  locationCountry: 'United States',
  locationRegion: '',
  status: 'draft',
  isFeatured: false,
  media: [],
  inspectionReferences: [],
  provenanceVerified: false,
  conditionNotes: '',
  conditionReportUrl: '',
  vin: '',
};

export function VehicleForm({
  mode,
  slug,
  initial,
}: {
  mode: 'create' | 'edit';
  slug?: string;
  initial?: VehicleFormValues;
}) {
  const router = useRouter();
  const { notify } = useSite();
  const values = initial ?? EMPTY_VEHICLE;

  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mediaText, setMediaText] = useState(values.media.map((item) => item.url).join('\n'));
  const [referencesText, setReferencesText] = useState(values.inspectionReferences.join('\n'));

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;
    setPending(true);
    setError(null);

    const form = new FormData(event.currentTarget);
    const text = (key: string) => String(form.get(key) ?? '').trim();
    const number = (key: string) => Number(form.get(key) ?? 0);

    const payload = {
      make: text('make'),
      model: text('model'),
      year: number('year'),
      title: text('title'),
      description: text('description'),
      price: number('price'),
      currency: text('currency'),
      mileage: number('mileage'),
      mileageUnit: text('mileageUnit'),
      bodyStyle: text('bodyStyle'),
      fuelType: text('fuelType'),
      transmission: text('transmission'),
      locationCountry: text('locationCountry'),
      locationRegion: text('locationRegion'),
      status: text('status'),
      isFeatured: form.get('isFeatured') === 'on',
      provenanceVerified: form.get('provenanceVerified') === 'on',
      media: mediaText
        .split('\n')
        .map((line) => line.trim())
        .filter(Boolean)
        .map((url) => ({ url, alt: text('title') })),
      inspectionReferences: referencesText
        .split('\n')
        .map((line) => line.trim())
        .filter(Boolean),
      conditionNotes: text('conditionNotes') || undefined,
      conditionReportUrl: text('conditionReportUrl') || undefined,
      vin: text('vin') || undefined,
    };

    const endpoint =
      mode === 'create'
        ? '/api/vehicles'
        : `/api/vehicles/${encodeURIComponent(slug ?? '')}`;

    try {
      const response = await fetch(endpoint, {
        method: mode === 'create' ? 'POST' : 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const body = (await response.json().catch(() => ({}))) as {
        success?: boolean;
        message?: string;
        details?: { fieldErrors?: Record<string, string[]> };
      };

      if (!response.ok || !body.success) {
        const first = body.details?.fieldErrors
          ? Object.values(body.details.fieldErrors)[0]?.[0]
          : undefined;
        setError(first ?? body.message ?? 'Could not save the vehicle.');
        setPending(false);
        return;
      }

      notify(mode === 'create' ? 'Vehicle created' : 'Vehicle updated');
      router.push('/admin/vehicles');
      router.refresh();
    } catch {
      setError('Network error. Please try again.');
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-8" noValidate>
      <section className="rounded-panel border border-line bg-surface/50 p-6">
        <h2 className="font-display text-lg font-600 text-heading">Identity</h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <Field id="make" label="Make">
            <Input id="make" name="make" required defaultValue={values.make} placeholder="Porsche" />
          </Field>
          <Field id="model" label="Model">
            <Input id="model" name="model" required defaultValue={values.model} placeholder="911 GT3" />
          </Field>
          <Field id="year" label="Year">
            <Input
              id="year"
              name="year"
              type="number"
              min={1900}
              max={new Date().getFullYear() + 2}
              required
              defaultValue={values.year}
            />
          </Field>
          <Field id="title" label="Listing title">
            <Input
              id="title"
              name="title"
              required
              minLength={4}
              defaultValue={values.title}
              placeholder="2022 Porsche 911 GT3 (992)"
            />
          </Field>
        </div>
        <div className="mt-4">
          <Field id="description" label="Description" hint="At least 20 characters">
            <Textarea id="description" name="description" required minLength={20} defaultValue={values.description} />
          </Field>
        </div>
      </section>

      <section className="rounded-panel border border-line bg-surface/50 p-6">
        <h2 className="font-display text-lg font-600 text-heading">Price and specification</h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Field id="price" label="Price">
            <Input id="price" name="price" type="number" min={1} step="0.01" required defaultValue={values.price} />
          </Field>
          <Field id="currency" label="Currency">
            <Select id="currency" name="currency" defaultValue={values.currency}>
              {CURRENCIES.map((code) => (
                <option key={code} value={code}>
                  {code}
                </option>
              ))}
            </Select>
          </Field>
          <Field id="mileage" label="Mileage">
            <Input id="mileage" name="mileage" type="number" min={0} required defaultValue={values.mileage} />
          </Field>
          <Field id="mileageUnit" label="Mileage unit">
            <Select id="mileageUnit" name="mileageUnit" defaultValue={values.mileageUnit}>
              <option value="mi">miles</option>
              <option value="km">kilometres</option>
            </Select>
          </Field>
          <Field id="bodyStyle" label="Body style">
            <Select id="bodyStyle" name="bodyStyle" defaultValue={values.bodyStyle}>
              {BODY_STYLES.map((style) => (
                <option key={style} value={style}>
                  {style}
                </option>
              ))}
            </Select>
          </Field>
          <Field id="fuelType" label="Fuel">
            <Select id="fuelType" name="fuelType" defaultValue={values.fuelType}>
              {FUELS.map((fuel) => (
                <option key={fuel} value={fuel}>
                  {fuel}
                </option>
              ))}
            </Select>
          </Field>
          <Field id="transmission" label="Transmission">
            <Select id="transmission" name="transmission" defaultValue={values.transmission}>
              {TRANSMISSIONS.map((transmission) => (
                <option key={transmission} value={transmission}>
                  {transmission}
                </option>
              ))}
            </Select>
          </Field>
          <Field id="locationCountry" label="Country">
            <Input id="locationCountry" name="locationCountry" required defaultValue={values.locationCountry} />
          </Field>
          <Field id="locationRegion" label="Region / state">
            <Input id="locationRegion" name="locationRegion" required defaultValue={values.locationRegion} />
          </Field>
        </div>
      </section>

      <section className="rounded-panel border border-line bg-surface/50 p-6">
        <h2 className="font-display text-lg font-600 text-heading">Photos and provenance</h2>
        <div className="mt-5 space-y-4">
          <Field id="media" label="Photo URLs" hint="One per line; /vehicles/name.webp or https://…">
            <Textarea
              id="media"
              value={mediaText}
              onChange={(event) => setMediaText(event.target.value)}
              placeholder={'/vehicles/2022-porsche-911-gt3.webp'}
              className="font-mono text-xs"
            />
          </Field>
          <Field id="references" label="Inspection references" hint="One per line">
            <Textarea
              id="references"
              value={referencesText}
              onChange={(event) => setReferencesText(event.target.value)}
              placeholder={'180-point inspection, 14 March 2026 — no findings'}
              className="font-mono text-xs"
            />
          </Field>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field id="conditionNotes" label="Condition notes">
              <Textarea id="conditionNotes" name="conditionNotes" defaultValue={values.conditionNotes ?? ''} />
            </Field>
            <div className="space-y-4">
              <Field id="conditionReportUrl" label="Condition report URL">
                <Input
                  id="conditionReportUrl"
                  name="conditionReportUrl"
                  type="url"
                  defaultValue={values.conditionReportUrl ?? ''}
                  placeholder="https://…"
                />
              </Field>
              <Field id="vin" label="VIN">
                <Input id="vin" name="vin" defaultValue={values.vin ?? ''} maxLength={32} />
              </Field>
            </div>
          </div>
          <div className="flex flex-wrap gap-6">
            <label className="flex items-center gap-2 text-sm text-body/85">
              <input
                type="checkbox"
                name="provenanceVerified"
                defaultChecked={values.provenanceVerified}
                className="size-4 rounded border-line bg-canvas accent-primary"
              />
              Provenance verified
            </label>
            <label className="flex items-center gap-2 text-sm text-body/85">
              <input
                type="checkbox"
                name="isFeatured"
                defaultChecked={values.isFeatured}
                className="size-4 rounded border-line bg-canvas accent-primary"
              />
              Feature on the home page
            </label>
          </div>
        </div>
      </section>

      <section className="rounded-panel border border-line bg-surface/50 p-6">
        <h2 className="font-display text-lg font-600 text-heading">Publishing</h2>
        <div className="mt-5 max-w-xs">
          <Field id="status" label="Status" hint="Only active cars appear in the storefront">
            <Select id="status" name="status" defaultValue={values.status}>
              {STATUSES.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </Select>
          </Field>
        </div>
      </section>

      {error && (
        <p role="alert" className="rounded-control border border-red-500/40 bg-red-500/5 px-4 py-3 text-sm text-red-300">
          {error}
        </p>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <Button type="submit" disabled={pending}>
          {pending ? (
            <>
              <Loader2 className="size-4 animate-spin" aria-hidden="true" />
              Saving…
            </>
          ) : (
            <>
              <Save className="size-4" aria-hidden="true" />
              {mode === 'create' ? 'Create vehicle' : 'Save changes'}
            </>
          )}
        </Button>
        <Button type="button" variant="ghost" onClick={() => router.push('/admin/vehicles')}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
