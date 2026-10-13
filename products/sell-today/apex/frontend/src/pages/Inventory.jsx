import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import VehicleCard from '../components/vehicle/VehicleCard';
import InventoryFilters from '../components/vehicle/InventoryFilters';
import vehicleApi from '../services/vehicleApi';

export default function Inventory() {
  const [params, setParams] = useSearchParams();
  const filters = Object.fromEntries(params.entries());
  const { data, isPending, isError, refetch, isFetching } = useQuery({
    queryKey: ['vehicles', filters],
    queryFn: ({ signal }) => vehicleApi.list(filters, { signal }),
  });

  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main id="main-content" className="mx-auto w-full max-w-7xl px-6 py-14 lg:py-20">
        <header className="mb-8 max-w-3xl">
          <p className="section-eyebrow">Apex Motor Collective</p>
          <h1 className="section-heading mt-2">The collection</h1>
          <p className="mt-4 leading-relaxed text-slate-500">Explore vehicles currently listed by our dealership. Listing currency and details are provided per vehicle.</p>
        </header>
        <InventoryFilters />
        {isPending && <p className="py-12 text-center" role="status">Loading available vehicles…</p>}
        {isError && <div className="py-12 text-center" role="alert"><p>We couldn’t load the collection.</p><button type="button" onClick={() => refetch()} className="btn-outline mt-4">Try again</button></div>}
        {!isPending && !isError && data?.items?.length === 0 && <p className="py-12 text-center text-slate-500">No vehicles match these filters. Try adjusting your search.</p>}
        {!!data?.items?.length && <>
          <p className="mt-6 text-sm text-slate-500" aria-live="polite">{data.total} {data.total === 1 ? 'vehicle' : 'vehicles'}{isFetching ? ' · Updating…' : ''}</p>
          <div className="mt-5 grid gap-6 md:grid-cols-2 lg:grid-cols-3">{data.items.map((vehicle) => <VehicleCard key={vehicle.id} vehicle={vehicle} />)}</div>
          <nav aria-label="Inventory pages" className="mt-10 flex items-center justify-center gap-4">
            <button type="button" className="btn-outline" disabled={data.page <= 1 || isFetching} onClick={() => { const next = new URLSearchParams(params); next.set('page', String(data.page - 1)); setParams(next); }}>Previous</button>
            <span aria-current="page">Page {data.page}</span>
            <button type="button" className="btn-outline" disabled={!data.hasMore || isFetching} onClick={() => { const next = new URLSearchParams(params); next.set('page', String(data.page + 1)); setParams(next); }}>Next</button>
          </nav>
        </>}
      </main>
      <Footer />
    </div>
  );
}
