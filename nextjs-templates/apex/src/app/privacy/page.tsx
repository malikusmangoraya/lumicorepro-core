import type { Metadata } from 'next';
import { Section } from '@/components/ui/section';

export const metadata: Metadata = {
  title: 'Privacy policy',
  description: 'What Apex Motor Collective collects, why, and how to have it removed.',
  alternates: { canonical: '/privacy' },
};

const sections = [
  {
    title: 'What we collect',
    body: 'When you send an enquiry we store your name, email, optional phone number and the message you wrote. When you create an account we additionally store a password hash. We do not buy contact lists and we do not run third-party advertising pixels on this site.',
  },
  {
    title: 'Why we collect it',
    body: 'To answer your enquiry, to arrange a viewing or inspection, and to keep a record of the transaction if you buy. Nothing else. Enquiry messages are visible only to the Apex team handling your case.',
  },
  {
    title: 'How long we keep it',
    body: 'Enquiries are kept for 24 months after the last contact so an ongoing search is not lost. Account data is kept until you delete the account. Transaction records are kept for seven years because tax law requires it.',
  },
  {
    title: 'Who we share it with',
    body: 'Only the parties required to complete a transaction: the inspection workshop, the transport company and the registration agent. We never sell data. Payment details are handled entirely by the payment provider and never reach our servers.',
  },
  {
    title: 'Your rights',
    body: 'You can export every record we hold about you, correct it, or delete it from the account page. Deletion removes the account and personal data; anonymised transaction records remain for the accounting period required by law.',
  },
  {
    title: 'Cookies',
    body: 'We set one HttpOnly session cookie when you sign in. It is required for authentication and is not used for tracking or advertising. There is no third-party cookie on this site.',
  },
];

export default function PrivacyPage() {
  return (
    <Section className="max-w-3xl">
      <p className="section-eyebrow">Legal</p>
      <h1 className="mt-3 font-display text-3xl font-700 text-heading sm:text-4xl">
        Privacy policy
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

      <p className="mt-10 border-t border-line/70 pt-6 text-sm text-muted">
        Questions about this policy: <a href="mailto:privacy@apex.com" className="text-accent hover:underline">privacy@apex.com</a>
      </p>
    </Section>
  );
}
