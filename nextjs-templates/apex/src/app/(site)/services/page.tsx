import type { Metadata } from 'next';
import Image from 'next/image';
import { Check } from 'lucide-react';
import { Section, SectionHeading } from '@/components/ui/section';
import { ButtonLink } from '@/components/ui/button';

export const metadata: Metadata = {
  title: 'Services',
  description:
    'Pre-purchase inspection, provenance research, private viewings, test drives, ownership preparation and enclosed delivery.',
  alternates: { canonical: '/services' },
};

const services = [
  {
    title: 'Pre-purchase inspection',
    summary:
      'A 180-point mechanical and cosmetic inspection by a marque specialist, with photos of every finding.',
    perks: ['Compression and leak-down where relevant', 'Paint depth readings panel by panel', 'Written report within 48 hours'],
  },
  {
    title: 'Provenance research',
    summary:
      'Ownership chain, service history and factory options verified against manufacturer records and independent archives.',
    perks: ['VIN decoded against the factory build sheet', 'Service book and invoice cross-check', 'Documented gaps stated, not hidden'],
  },
  {
    title: 'Private viewings',
    summary:
      'See the car in a closed workshop, on a lift, with a specialist present — not in a public car park.',
    perks: ['Evening and weekend slots', 'Underbody and lift inspection', 'No time pressure, no minders'],
  },
  {
    title: 'Test drives',
    summary:
      'A route that actually exercises the car: cold start, town, motorway and a braking section.',
    perks: ['Insured demonstration drive', 'Cold-start observation', 'Route chosen to surface faults'],
  },
  {
    title: 'Ownership preparation',
    summary:
      'Registration, transfer paperwork, insurance introductions and a first service plan before you collect.',
    perks: ['Title and lien check', 'Registration handled end to end', 'First-service schedule set'],
  },
  {
    title: 'Enclosed delivery',
    summary:
      'Covered transport with photo evidence at collection and delivery, anywhere in the continental US.',
    perks: ['Enclosed, strapped transport', 'Photo record at both ends', 'Door-to-door, fully insured'],
  },
];

export default function ServicesPage() {
  return (
    <>
      <Section>
        <SectionHeading as="h1"
          eyebrow="Services"
          title="Everything between “I like that car” and the keys in your hand"
          description="Buying a performance car is a chain of small decisions. We run the whole chain, so nothing depends on a seller's goodwill."
        />

        <div className="mt-10 grid gap-5 md:grid-cols-2">
          {services.map((service) => (
            <article key={service.title} className="rounded-panel border border-line bg-surface/50 p-6">
              <h2 className="font-display text-lg font-600 text-heading">{service.title}</h2>
              <p className="mt-2 text-sm leading-relaxed text-muted">{service.summary}</p>
              <ul className="mt-4 space-y-2">
                {service.perks.map((perk) => (
                  <li key={perk} className="flex items-start gap-2 text-sm text-body/85">
                    <Check className="mt-0.5 size-4 shrink-0 text-accent" aria-hidden="true" />
                    {perk}
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </Section>

      <Section className="pt-0">
        <div className="relative aspect-[21/9] overflow-hidden rounded-panel border border-line bg-canvas">
          <Image
            src="/editorial/handover.webp"
            alt="A car being handed over to its new owner at dusk"
            fill
            sizes="100vw"
            className="object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-canvas/80 to-transparent" aria-hidden="true" />
          <p className="absolute bottom-4 left-5 right-5 text-sm text-heading sm:bottom-6 sm:left-8">
            The handover: keys, paperwork and a specialist who answers the phone afterwards too.
          </p>
        </div>
      </Section>

      <Section className="pt-0">
        <div className="rounded-panel border border-primary/30 bg-primary/5 px-6 py-12 text-center sm:px-12">
          <h2 className="text-balance font-display text-2xl font-700 text-heading sm:text-3xl">
            Not sure which service you need?
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-sm leading-relaxed text-muted">
            Describe the car and the decision in front of you. We will tell you which part of the
            chain matters, and which does not.
          </p>
          <div className="mt-7 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/contact" size="lg">
              Ask a specialist
            </ButtonLink>
            <ButtonLink href="/inventory" size="lg" variant="outline">
              Browse inventory
            </ButtonLink>
          </div>
        </div>
      </Section>
    </>
  );
}
