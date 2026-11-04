import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ArrowLeft, FileText, ShieldCheck } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Panel } from '@/components/ui/card';
import { Section } from '@/components/ui/section';
import { Breadcrumbs } from '@/components/layout/breadcrumbs';
import { VehicleGallery } from '@/components/vehicle/vehicle-gallery';
import { FinanceCalculator } from '@/components/vehicle/finance-calculator';
import { SaveButton } from '@/components/vehicle/save-button';
import { CompareButton } from '@/components/vehicle/compare-button';
import { ShareButton } from '@/components/vehicle/share-button';
import { InquiryForm } from '@/components/vehicle/inquiry-form';
import { RecentlyViewed } from '@/components/vehicle/recently-viewed';
import { RecentlyViewedTracker } from '@/components/vehicle/recently-viewed-tracker';
import { getVehicleBySlug } from '@/lib/vehicles';
import { formatCurrency, formatMileage } from '@/lib/utils';

export const dynamic = 'force-dynamic';

type Params = Promise<{ slug: string }>;

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000';

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { slug } = await params;
  const vehicle = await getVehicleBySlug(slug);
  if (!vehicle) return { title: 'Vehicle not found' };
  return {
    title: vehicle.title,
    description: `${vehicle.year} ${vehicle.make} ${vehicle.model} — ${formatMileage(
      vehicle.mileage,
      vehicle.mileageUnit,
    )}, ${vehicle.locationRegion}, ${vehicle.locationCountry}.`,
    alternates: { canonical: `/inventory/${vehicle.slug}` },
    openGraph: {
      title: vehicle.title,
      images: vehicle.media[0] ? [{ url: vehicle.media[0].url }] : undefined,
    },
  };
}

export default async function VehicleDetailPage({ params }: { params: Params }) {
  const { slug } = await params;
  const vehicle = await getVehicleBySlug(slug);
  if (!vehicle) notFound();

  const specs = [
    { label: 'Year', value: String(vehicle.year) },
    { label: 'Mileage', value: formatMileage(vehicle.mileage, vehicle.mileageUnit) },
    { label: 'Body style', value: vehicle.bodyStyle },
    { label: 'Fuel', value: vehicle.fuelType },
    { label: 'Transmission', value: vehicle.transmission },
    { label: 'Location', value: `${vehicle.locationRegion}, ${vehicle.locationCountry}` },
    ...(vehicle.vin ? [{ label: 'VIN', value: vehicle.vin }] : []),
  ];

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Car',
    name: vehicle.title,
    brand: { '@type': 'Brand', name: vehicle.make },
    model: vehicle.model,
    vehicleModelDate: String(vehicle.year),
    bodyType: vehicle.bodyStyle,
    fuelType: vehicle.fuelType,
    vehicleTransmission: vehicle.transmission,
    mileageFromOdometer: {
      '@type': 'QuantitativeValue',
      value: vehicle.mileage,
      unitCode: vehicle.mileageUnit === 'km' ? 'KMT' : 'SMI',
    },
    ...(vehicle.vin ? { vehicleIdentificationNumber: vehicle.vin } : {}),
    image: vehicle.media.map((image) => `${siteUrl}${image.url}`),
    url: `${siteUrl}/inventory/${vehicle.slug}`,
    offers: {
      '@type': 'Offer',
      price: vehicle.price,
      priceCurrency: vehicle.currency,
      availability:
        vehicle.status === 'sold'
          ? 'https://schema.org/SoldOut'
          : 'https://schema.org/InStock',
      url: `${siteUrl}/inventory/${vehicle.slug}`,
    },
  };

  return (
    <>
      <Section>
        <Breadcrumbs
          items={[
            { href: '/', label: 'Home' },
            { href: '/inventory', label: 'Inventory' },
            { href: `/inventory/${vehicle.slug}`, label: vehicle.title },
          ]}
        />

        <Link
          href="/inventory"
          className="mt-4 inline-flex items-center gap-1.5 text-sm text-muted transition-colors hover:text-heading"
        >
          <ArrowLeft className="size-4" aria-hidden="true" />
          Back to inventory
        </Link>

        <div className="mt-6 grid gap-8 lg:grid-cols-[1.4fr_0.6fr]">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone="neutral">{vehicle.status}</Badge>
              {vehicle.provenanceVerified && (
                <Badge tone="success">
                  <ShieldCheck className="size-3" aria-hidden="true" />
                  Provenance verified
                </Badge>
              )}
            </div>

            <h1 className="mt-4 text-balance font-display text-3xl font-700 leading-tight text-heading sm:text-4xl">
              {vehicle.title}
            </h1>
            <p className="mt-2 text-sm text-muted">
              {vehicle.locationRegion}, {vehicle.locationCountry}
            </p>

            <div className="mt-6">
              <VehicleGallery media={vehicle.media} title={vehicle.title} />
            </div>

            <Panel className="mt-8 p-6">
              <h2 className="font-display text-lg font-600 text-heading">The car</h2>
              <p className="mt-3 whitespace-pre-line text-sm leading-relaxed text-body/85">
                {vehicle.description}
              </p>

              <dl className="mt-6 grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-3">
                {specs.map((spec) => (
                  <div key={spec.label}>
                    <dt className="text-xs uppercase tracking-[0.14em] text-muted">{spec.label}</dt>
                    <dd className="mt-1 text-sm font-medium text-heading">{spec.value}</dd>
                  </div>
                ))}
              </dl>

              {vehicle.inspectionReferences.length > 0 && (
                <div className="mt-6 border-t border-line/70 pt-4">
                  <h3 className="text-xs font-semibold uppercase tracking-[0.14em] text-heading">
                    Inspection references
                  </h3>
                  <ul className="mt-2 space-y-1.5 text-sm text-muted">
                    {vehicle.inspectionReferences.map((reference) => (
                      <li key={reference}>{reference}</li>
                    ))}
                  </ul>
                </div>
              )}

              {vehicle.conditionNotes && (
                <div className="mt-6 border-t border-line/70 pt-4">
                  <h3 className="text-xs font-semibold uppercase tracking-[0.14em] text-heading">
                    Condition notes
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted">
                    {vehicle.conditionNotes}
                  </p>
                </div>
              )}

              {vehicle.conditionReportUrl && (
                <a
                  href={vehicle.conditionReportUrl}
                  className="mt-5 inline-flex items-center gap-2 text-sm font-medium text-accent hover:underline"
                  target="_blank"
                  rel="noreferrer noopener"
                >
                  <FileText className="size-4" aria-hidden="true" />
                  Read the full condition report
                </a>
              )}
            </Panel>

            <div className="mt-8">
              <FinanceCalculator price={vehicle.price} currency={vehicle.currency} />
            </div>
          </div>

          <aside className="space-y-5 lg:sticky lg:top-24 lg:self-start">
            <Panel className="p-6">
              <p className="text-xs uppercase tracking-[0.14em] text-muted">Asking price</p>
              <p className="mt-1 font-display text-3xl font-700 text-accent">
                {formatCurrency(vehicle.price, vehicle.currency)}
              </p>
              <p className="mt-2 text-xs leading-relaxed text-muted">
                Taxes and registration are shown at checkout, never bundled into the listed price.
              </p>

              <div className="mt-5 grid grid-cols-2 gap-2">
                <SaveButton slug={vehicle.slug} title={vehicle.title} variant="full" />
                <CompareButton slug={vehicle.slug} title={vehicle.title} variant="full" />
              </div>
              <div className="mt-2">
                <ShareButton
                  title={vehicle.title}
                  url={`${siteUrl}/inventory/${vehicle.slug}`}
                />
              </div>
            </Panel>

            <Panel className="p-6">
              <h2 className="font-display text-lg font-600 text-heading">Enquire about this car</h2>
              <p className="mt-1 mb-5 text-sm leading-relaxed text-muted">
                A specialist replies within one business day. No obligation, no sales calls.
              </p>
              <InquiryForm vehicleId={vehicle.id} vehicleTitle={vehicle.title} />
            </Panel>
          </aside>
        </div>
      </Section>

      <RecentlyViewed excludeSlug={vehicle.slug} />
      <RecentlyViewedTracker slug={vehicle.slug} />

      <script
        type="application/ld+json"
        // Built from database fields only; no user input reaches this string.
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
    </>
  );
}
