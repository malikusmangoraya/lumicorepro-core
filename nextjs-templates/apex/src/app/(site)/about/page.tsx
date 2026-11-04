import type { Metadata } from 'next';
import Image from 'next/image';
import { Section, SectionHeading } from '@/components/ui/section';
import { ButtonLink } from '@/components/ui/button';
import { Stat } from '@/components/ui/card';

export const metadata: Metadata = {
  title: 'About',
  description:
    'Apex Motor Collective is a small team of specialists who inspect, document and deliver performance and collector cars.',
  alternates: { canonical: '/about' },
};

const values = [
  {
    number: '01',
    title: 'We only list what we would buy',
    body: 'The inventory is deliberately small. If a car does not pass inspection, it does not go on the site — no exceptions for a good story.',
  },
  {
    number: '02',
    title: 'Every claim is evidence',
    body: 'Mileage, provenance and options are checked against documents and the manufacturer record. If we cannot evidence it, we do not say it.',
  },
  {
    number: '03',
    title: 'One price, published',
    body: 'The listed price is the asking price. No "call for price", no auction-style games, no surprise fees at the desk.',
  },
  {
    number: '04',
    title: 'The handover matters',
    body: 'Enclosed transport, photo evidence at both ends, and a specialist who answers the phone after the sale as well as before it.',
  },
];

export default function AboutPage() {
  return (
    <>
      <Section>
        <div className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
          <div>
            <p className="section-eyebrow">About Apex</p>
            <h1 className="mt-4 text-balance font-display text-4xl font-700 leading-[1.08] text-heading sm:text-5xl">
              A small collective built around one idea: the car should be exactly as described.
            </h1>
            <p className="mt-5 max-w-xl text-pretty text-base leading-relaxed text-muted">
              Apex started because buying a performance car had become a test of endurance —
              listings with no history, prices that changed on the phone, and inspections that
              happened after the deposit. We built the opposite: a short, documented inventory and a
              single specialist who owns your purchase end to end.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <ButtonLink href="/inventory">See the inventory</ButtonLink>
              <ButtonLink href="/services" variant="outline">
                How we inspect
              </ButtonLink>
            </div>
          </div>

          <div className="space-y-4">
            <div className="relative aspect-[4/3] overflow-hidden rounded-panel border border-line bg-canvas">
              <Image
                src="/editorial/workshop.webp"
                alt="Two Apex specialists inspecting a car raised on a workshop lift"
                fill
                sizes="(max-width: 1024px) 100vw, 45vw"
                className="object-cover"
              />
            </div>
            <div className="rounded-panel border border-line bg-surface/60 p-6">
              <h2 className="font-display text-lg font-600 text-heading">The collective in numbers</h2>
              <div className="mt-4 grid grid-cols-2 gap-3">
                <Stat value="12 yrs" label="Trading" />
                <Stat value="1,900+" label="Cars placed" />
                <Stat value="48 hrs" label="Inspection" />
                <Stat value="4.9/5" label="Owner rating" />
              </div>
            </div>
          </div>
        </div>
      </Section>

      <Section className="pt-0">
        <SectionHeading
          eyebrow="What we hold ourselves to"
          title="Four rules that decide what gets listed"
          description="These are not marketing lines. They are the checklist every car passes before it appears on this site."
        />
        <div className="mt-10 grid gap-4 sm:grid-cols-2">
          {values.map((value) => (
            <article key={value.number} className="rounded-panel border border-line bg-surface/50 p-6">
              <span className="font-display text-sm font-700 text-accent">{value.number}</span>
              <h3 className="mt-3 font-display text-lg font-600 text-heading">{value.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{value.body}</p>
            </article>
          ))}
        </div>
      </Section>

      <Section className="pt-0">
        <div className="rounded-panel border border-primary/30 bg-primary/5 px-6 py-12 text-center sm:px-12">
          <h2 className="text-balance font-display text-2xl font-700 text-heading sm:text-3xl">
            Buying or selling, start with a conversation
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-sm leading-relaxed text-muted">
            Tell us the car you want or the car you have. A specialist will tell you honestly what
            it is worth and what it needs.
          </p>
          <div className="mt-7 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/contact" size="lg">
              Talk to a specialist
            </ButtonLink>
            <ButtonLink href="/pricing" size="lg" variant="outline">
              Membership options
            </ButtonLink>
          </div>
        </div>
      </Section>
    </>
  );
}
