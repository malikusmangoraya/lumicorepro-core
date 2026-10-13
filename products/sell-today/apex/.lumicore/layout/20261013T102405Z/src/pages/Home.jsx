import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { ArrowRight, CarFront, Gauge, ShieldCheck, Wrench } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import VehicleCard from '../components/vehicle/VehicleCard';
import vehicleApi from '../services/vehicleApi';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Home() {
  const { t } = useTranslation();
  const { data: inventory } = useQuery({
    queryKey: ['vehicles', { limit: 3, sort: 'newest' }],
    queryFn: ({ signal }) => vehicleApi.list({ limit: 3, sort: 'newest' }, { signal }),
  });
  const vehicles = inventory?.items || [];
  const services = [
    { icon: CarFront, title: 'Curated inventory', detail: 'Browse the vehicles currently listed by Apex and ask our team about availability.' },
    { icon: ShieldCheck, title: 'Vehicle information', detail: 'Review the details provided for each listing and request supporting information from our team.' },
    { icon: Wrench, title: 'Concierge ownership', detail: 'Speak with our team about viewings, preparation and the next steps for a vehicle.' },
  ];

  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main id="main-content">
        <section className="relative overflow-hidden bg-slate-950 text-white">
          <div className="absolute inset-0 opacity-35" aria-hidden="true">
            <img src="/images/extra-1.jpg" alt="" className="h-full w-full object-cover" />
          </div>
          <div className="absolute inset-0 bg-gradient-to-r from-slate-950 via-slate-950/90 to-slate-950/25" aria-hidden="true" />
          <div className="relative mx-auto grid max-w-7xl items-center gap-12 px-6 py-24 lg:min-h-[640px] lg:grid-cols-12 lg:py-28">
            <div className="lg:col-span-7">
              <p className="section-eyebrow !text-amber-300">{t('Home.automotive', 'APEX MOTOR COLLECTIVE')}</p>
              <h1 className="mt-5 max-w-3xl text-5xl font-black leading-[1.02] tracking-tight text-white sm:text-6xl lg:text-7xl">Find the car that feels like it was made for you.</h1>
              <p className="mt-6 max-w-xl text-lg leading-relaxed text-slate-200">Explore performance and collector cars, with clear vehicle details and a direct line to our team.</p>
              <div className="mt-9 flex flex-wrap gap-4">
                <Link to="/inventory" className="btn-primary !bg-amber-400 !text-slate-950">Explore the collection <ArrowRight className="h-4 w-4" /></Link>
                <Link to="/contact" className="btn-outline !border-white !text-white hover:!bg-white hover:!text-slate-950">Arrange a private viewing</Link>
              </div>
              <div className="mt-10 flex flex-wrap gap-x-8 gap-y-3 text-sm text-slate-300">
                <span className="inline-flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-amber-300" /> Vehicle details, clearly presented</span>
                <span className="inline-flex items-center gap-2"><Gauge className="h-4 w-4 text-amber-300" /> Speak directly with an advisor</span>
              </div>
            </div>
            <div className="lg:col-span-5 lg:justify-self-end">
              <div className="max-w-md border border-white/20 bg-black/40 p-6 backdrop-blur-sm">
                <p className="text-xs uppercase tracking-[.25em] text-amber-300">The Apex approach</p>
                <p className="mt-3 text-2xl font-semibold text-white">Know what is listed. Ask about what matters.</p>
                <p className="mt-3 text-sm leading-relaxed text-slate-300">Review available listing information and ask our team about history, condition and availability.</p>
              </div>
            </div>
          </div>
        </section>
        <section className="mx-auto max-w-7xl px-6 py-20 lg:py-28">
          <div className="mb-10 flex flex-wrap items-end justify-between gap-5">
            <div><p className="section-eyebrow">The collection</p><h2 className="section-heading mt-2">Explore the vehicles currently listed.</h2></div>
            <Link to="/inventory" className="btn-outline">Browse all vehicles <ArrowRight className="h-4 w-4" /></Link>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            {vehicles.map((vehicle) => <VehicleCard key={vehicle.id} vehicle={vehicle} />)}
            {vehicles.length === 0 && <p className="text-slate-500 md:col-span-3">No vehicles are currently listed. Contact an advisor to discuss a tailored search.</p>}
          </div>
        </section>
        <section className="bg-surface py-20">
          <div className="mx-auto max-w-7xl px-6"><div className="max-w-2xl"><p className="section-eyebrow">Beyond the sale</p><h2 className="section-heading mt-2">A considered experience, at every turn.</h2></div>
            <div className="mt-10 grid gap-6 md:grid-cols-3">{services.map(({ icon: Icon, title, detail }) => <article key={title} className="border-t-2 border-[var(--t-primary)] bg-canvas p-6"><Icon className="h-6 w-6 text-[var(--t-primary)]" aria-hidden="true"/><h3 className="mt-4 text-lg font-bold">{title}</h3><p className="mt-2 text-sm leading-relaxed text-slate-500">{detail}</p></article>)}</div>
          </div>
        </section>
        <section className="mx-auto max-w-5xl px-6 py-20 text-center"><h2 className="section-heading">Your next chapter starts behind the wheel.</h2><p className="mx-auto mt-4 max-w-xl text-slate-500">Tell our automotive concierge what you are looking for. We will discuss the next steps and any matching vehicles currently available.</p><Link to="/contact" className="btn-primary mt-7">Speak with an advisor <ArrowRight className="h-4 w-4" /></Link></section>
      </main>
      <Footer />
    </div>
  );
}
