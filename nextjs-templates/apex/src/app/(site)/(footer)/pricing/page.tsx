import type { Metadata } from 'next';
import { PricingTable } from '@/components/pricing/pricing-table';
import { Section, SectionHeading } from '@/components/ui/section';

export const metadata: Metadata = {
  title: 'Membership',
  description: 'Three membership tiers for collectors and dealers who buy more than once.',
  alternates: { canonical: '/pricing' },
};

const faqs = [
  {
    question: 'Can I cancel at any time?',
    answer:
      'Yes. Cancel from the account page and the membership runs to the end of the paid period. There is no cancellation fee and no retention call.',
  },
  {
    question: 'Is the membership required to buy a car?',
    answer:
      'No. Every listed car can be enquired about without a membership. Membership is for people who want inspection coordination, unlimited history reports and price alerts on an ongoing basis.',
  },
  {
    question: 'What does “unlimited history reports” actually mean?',
    answer:
      'You can request a provenance report on any VIN as often as you like while the membership is active. The reports are produced by our research team, not resold from a third-party database.',
  },
  {
    question: 'Do you offer refunds?',
    answer:
      'If a report or inspection did not meet the standard described here, we refund that month. We do not refund a membership simply because you did not use it.',
  },
];

export default function PricingPage() {
  return (
    <>
      <Section>
        <SectionHeading as="h1"
          align="center"
          eyebrow="Membership"
          title="Buy once, or buy often"
          description="The storefront is open to everyone. Membership is for collectors and dealers who want the research and inspection work handled as a standing service."
        />
        <div className="mt-12">
          <PricingTable />
        </div>
      </Section>

      <Section className="pt-0">
        <SectionHeading
          eyebrow="Questions"
          title="Before you choose"
          description="The short answers to the things people ask before signing up."
        />
        <div className="mt-8 max-w-3xl divide-y divide-line/70 rounded-panel border border-line bg-surface/40">
          {faqs.map((faq) => (
            <details key={faq.question} className="group p-5">
              <summary className="cursor-pointer list-none font-medium text-heading marker:hidden">
                <span className="flex items-center justify-between gap-4">
                  {faq.question}
                  <span
                    aria-hidden="true"
                    className="text-accent transition-transform group-open:rotate-45"
                  >
                    +
                  </span>
                </span>
              </summary>
              <p className="mt-3 text-sm leading-relaxed text-muted">{faq.answer}</p>
            </details>
          ))}
        </div>
      </Section>
    </>
  );
}
