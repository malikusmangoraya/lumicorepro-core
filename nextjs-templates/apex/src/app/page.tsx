import { ArrowRight, BadgeCheck, Gauge, Handshake, ShieldCheck, Truck } from 'lucide-react';
import { ButtonLink } from '@/components/ui/button';
import { Section, SectionHeading } from '@/components/ui/section';
import { Stat } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { VehicleCard } from '@/components/vehicle/vehicle-card';
import { listFeaturedVehicles } from '@/lib/vehicles';

export const dynamic = 'force-dynamic';

const checklist = [
  'Every car inspected before it is listed',
  'Provenance and service history verified',
  'Fixed, published price — no haggling theatre',
  'Enclosed delivery to your door',
];

const pillars = [
  {
    icon: BadgeCheck,
    title: 'Verified provenance',
    body: 'Service books, ownership chains and factory options are checked against the manufacturer record before a listing goes live.',
  },
  {
    icon: Gauge,
    title: 'Driven, not just stored',
    body: 'Every car in the collective is road-tested by our own specialists. The notes you read are the notes they wrote.',
  },
  {
    icon: Handshake,
    title: 'One point of contact',
    body: 'A single specialist handles the enquiry, the viewing, the paperwork and the handover. No call-centre relay.',
  },
  {
    icon: Truck,
    title: 'Enclosed delivery',
    body: 'Covered transport with photo evidence at collection and delivery, anywhere in the continental United States.',
  },
];

export default async function HomePage() {
  const featured = await listFeaturedVehicles(3);

  return (
    <>
      <section className="hero-aurora border-b border-line/60">
        <div className="surface-grid absolute inset-0 -z-10" aria-hidden="true" />
        <div className="mx-auto grid max-w-6xl gap-12 px-4 py-20 sm:px-6 sm:py-28 lg:grid-cols-[1.15fr_0.85fr] lg:items-center">
          <div>
            <p className="section-eyebrow">Drive something exceptional</p>
            <h1 className="mt-4 max-w-xl text-balance font-display text-4xl font-700 leading-[1.05] text-heading sm:text-6xl">
              Your next car, found faster.
            </h1>
            <p className="mt-5 max-w-lg text-pretty text-base leading-relaxed text-muted sm:text-lg">
              A curated collective of performance and collector cars. Inspected, documented and
              priced honestly — so the only decision left is which one to drive first.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-3">
              <ButtonLink href="/inventory" size="lg">
                Browse the inventory
                <ArrowRight className="size-4" aria-hidden="true" />
              </ButtonLink>
              <ButtonLink href="/services" size="lg" variant="outline">
                How we inspect
              </ButtonLink>
            </div>

            <dl className="mt-10 flex flex-wrap gap-x-8 gap-y-3 text-sm text-muted">
              <div className="flex items-center gap-2">
                <ShieldCheck className="size-4 text-accent" aria-hidden="true" />
                <dt className="sr-only">Provenance</dt>
                <dd>Provenance on every listing</dd>
              </div>
              <div className="flex items-center gap-2">
                <Gauge className="size-4 text-accent" aria-hidden="true" />
                <dt className="sr-only">Testing</dt>
                <dd>Road-tested by specialists</dd>
              </div>
            </dl>
          </div>

          <div className="rounded-panel border border-line bg-surface/70 p-6 shadow-panel backdrop-blur">
            <div className="flex items-center justify-between">
              <h2 className="font-display text-lg font-600 text-heading">What you get</h2>
              <Badge tone="primary">Every car</Badge>
            </div>
            <ul className="mt-5 space-y-3">
              {checklist.map((item) => (
                <li key={item} className="flex items-start gap-2.5 text-sm text-body/85">
                  <BadgeCheck className="mt-0.5 size-4 shrink-0 text-accent" aria-hidden="true" />
                  {item}
                </li>
              ))}
            </ul>
            <p className="mt-6 border-t border-line/70 pt-4 text-xs leading-relaxed text-muted">
              Listed prices are the price you pay. Taxes and registration are shown separately at
              checkout, never buried.
            </p>
          </div>
        </div>
      </section>

      <Section>
        <SectionHeading
          eyebrow="Why Apex"
          title="A dealership built like a specialist, priced like a marketplace"
          description="We keep the inventory small on purpose. Every car earns its place, and every claim on this site is one we can evidence."
        />
        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {pillars.map((pillar) => (
            <article
              key={pillar.title}
              className="rounded-panel border border-line bg-surface/50 p-5 transition-colors hover:border-primary/40"
            >
              <pillar.icon className="size-5 text-accent" aria-hidden="true" />
              <h3 className="mt-4 font-display text-base font-600 text-heading">{pillar.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{pillar.body}</p>
            </article>
          ))}
        </div>
      </Section>

      <Section className="pt-0">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Stat value="12 yrs" label="Buying collector cars" />
          <Stat value="48 hrs" label="Average inspection turnaround" />
          <Stat value="1,900+" label="Cars placed with owners" />
          <Stat value="4.9/5" label="Owner rating, 380 reviews" />
        </div>
      </Section>

      <Section className="pt-0">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <SectionHeading
            eyebrow="In the collective"
            title="Recently listed"
            description="A live view of the current inventory. Filter by make, budget or mileage on the inventory page."
          />
          <ButtonLink href="/inventory" variant="outline" size="sm">
            View all
            <ArrowRight className="size-3.5" aria-hidden="true" />
          </ButtonLink>
        </div>

        {featured.length > 0 ? (
          <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {featured.map((vehicle) => (
              <VehicleCard key={vehicle.id} vehicle={vehicle} />
            ))}
          </div>
        ) : (
          <div className="mt-8 rounded-panel border border-dashed border-line bg-surface/40 px-6 py-14 text-center">
            <h3 className="font-600 text-heading">The inventory is being prepared</h3>
            <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-muted">
              Run <code className="rounded bg-canvas px-1.5 py-0.5 text-accent">npm run db:setup</code>{' '}
              to create the database and seed six cars, then reload this page.
            </p>
          </div>
        )}
      </Section>

      <Section className="pt-0">
        <div className="rounded-panel border border-primary/30 bg-primary/5 px-6 py-12 text-center sm:px-12">
          <h2 className="text-balance font-display text-2xl font-700 text-heading sm:text-3xl">
            Tell us what you are looking for
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-sm leading-relaxed text-muted">
            Not everything we source is listed. Send us the spec and a specialist will search the
            network, including cars that never reach the public inventory.
          </p>
          <div className="mt-7 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/contact" size="lg">
              Start a search
            </ButtonLink>
            <ButtonLink href="/pricing" size="lg" variant="outline">
              See membership
            </ButtonLink>
          </div>
        </div>
      </Section>
    </>
  );
}
