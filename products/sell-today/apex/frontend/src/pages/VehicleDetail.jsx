import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import LazyImage from '../components/common/LazyImage';
import VehicleInquiryForm from '../components/vehicle/VehicleInquiryForm';
import vehicleApi from '../services/vehicleApi';

function formatPrice(amount, currency) {
  try { return new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(Number(amount)); }
  catch { return `${amount} ${currency}`; }
}

export default function VehicleDetail() {
  const { slug } = useParams();
  const { data: vehicle, isPending, isError, refetch } = useQuery({
    queryKey: ['vehicle', slug],
    queryFn: ({ signal }) => vehicleApi.getBySlug(slug, { signal }),
  });
  const media = Array.isArray(vehicle?.media) ? vehicle.media : [];
  const gallery = media.map((item) => typeof item === 'string' ? { url: item } : item).filter((item) => item?.url);

  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main id="main-content" className="mx-auto w-full max-w-7xl px-6 py-14">
        <Link to="/inventory" className="text-sm font-semibold text-[var(--t-primary)]">← Back to collection</Link>
        {isPending && <p role="status" className="py-16 text-center">Loading vehicle details…</p>}
        {isError && <div role="alert" className="py-16 text-center"><p>This vehicle could not be loaded. It may no longer be available.</p><button type="button" onClick={() => refetch()} className="btn-outline mt-4">Try again</button></div>}
        {vehicle && <>
          <header className="my-8 max-w-4xl"><p className="section-eyebrow">{[vehicle.location_region, vehicle.location_country].filter(Boolean).join(' · ')}</p><h1 className="section-heading mt-2">{vehicle.title}</h1><p className="mt-3 text-xl font-semibold">{formatPrice(vehicle.price, vehicle.currency)} <span className="text-sm font-normal text-slate-500">· listed in {vehicle.currency}</span></p></header>
          {gallery.length > 0 ? <div className="grid gap-4 md:grid-cols-2">{gallery.map((image, index) => <LazyImage key={`${image.url}-${index}`} src={image.url} alt={image.alt || `${vehicle.title}, view ${index + 1}`} ratio="16 / 10" priority={index === 0} />)}</div> : <div className="flex aspect-video items-center justify-center bg-slate-100 text-slate-500" role="img" aria-label="No vehicle images available">Images not available</div>}
          <div className="mt-10 grid gap-10 lg:grid-cols-[1fr_24rem]">
            <section aria-labelledby="vehicle-details-heading"><h2 id="vehicle-details-heading" className="text-2xl font-bold">Vehicle details</h2>{vehicle.description && <p className="mt-4 whitespace-pre-line leading-relaxed text-slate-600">{vehicle.description}</p>}
              <dl className="mt-6 grid gap-x-8 gap-y-4 border-y border-[var(--t-border)] py-6 sm:grid-cols-2">{[["Year", vehicle.year], ["Make", vehicle.make], ["Model", vehicle.model], ["Mileage", vehicle.mileage == null ? null : `${Number(vehicle.mileage).toLocaleString()} ${vehicle.mileage_unit || 'km'}`], ["Body style", vehicle.body_style], ["Fuel", vehicle.fuel_type], ["Transmission", vehicle.transmission], ["Condition", vehicle.condition_notes], ["Provenance", vehicle.provenance_verified ? 'Verified by the dealership' : null]].filter(([, value]) => value !== null && value !== undefined && value !== '').map(([label, value]) => <div key={label}><dt className="text-xs uppercase tracking-widest text-slate-500">{label}</dt><dd className="mt-1 font-medium">{String(value)}</dd></div>)}</dl>
              {vehicle.condition_report_url && <a href={vehicle.condition_report_url} target="_blank" rel="noreferrer" className="mt-5 inline-block underline">View condition report</a>}
            </section>
            <VehicleInquiryForm vehicleId={vehicle.id} />
          </div>
        </>}
      </main>
      <Footer />
    </div>
  );
}
