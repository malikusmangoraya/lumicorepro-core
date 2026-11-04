import type { Metadata } from 'next';
import { Section } from '@/components/ui/section';

export const metadata: Metadata = {
  title: 'Terms of service',
  description: 'The terms that apply to using the Apex Motor Collective storefront.',
  alternates: { canonical: '/terms' },
};

const sections = [
  {
    title: 'Acceptance',
    body: 'By using this site you agree to these terms. If you do not agree, do not use the site. These terms apply to browsing, enquiring and buying.',
  },
  {
    title: 'Permitted use',
    body: 'You may browse, enquire and buy for personal or business use. You may not scrape the inventory at volume, republish listing photographs as your own, or use the site to send unsolicited messages.',
  },
  {
    title: 'Listings and availability',
    body: 'Every listing describes a specific car and is accurate to the best of our knowledge at the time of publication. A car can be sold or withdrawn while a listing remains visible; we will tell you promptly if that happens. Listed prices are asking prices in the stated currency and are never converted at display time.',
  },
  {
    title: 'Enquiries and accounts',
    body: 'You are responsible for the accuracy of the details you send and for keeping your account password confidential. We may suspend an account that is used to abuse the enquiry system.',
  },
  {
    title: 'Limitation of liability',
    body: 'Inspection reports and provenance research are professional opinions based on the evidence available at the time, not guarantees of future condition. Our liability for any claim is limited to the amount you paid us for the relevant service, except where the law does not allow that limitation.',
  },
  {
    title: 'Governing law',
    body: 'These terms are governed by the laws of the State of California. Disputes are resolved in the courts of Los Angeles County, unless a mandatory consumer protection law gives you a different forum.',
  },
];

export default function TermsPage() {
  return (
    <Section className="max-w-3xl">
      <p className="section-eyebrow">Legal</p>
      <h1 className="mt-3 font-display text-3xl font-700 text-heading sm:text-4xl">
        Terms of service
      </h1>
      <p className="mt-3 text-sm text-muted">Last updated 29 October 2026</p>

      <div className="mt-10 space-y-8">
        {sections.map((section) => (
          <section key={section.title}>
            <h2 className="font-display text-lg font-600 text-heading">{section.title}</h2>
            <p className="mt-2 text-sm leading-relaxed text-body/80">{section.body}</p>
          </section>
        ))}
      </div>
    </Section>
  );
}
