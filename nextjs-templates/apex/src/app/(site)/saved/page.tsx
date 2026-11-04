import type { Metadata } from 'next';
import { Section, SectionHeading } from '@/components/ui/section';
import { SavedList } from '@/components/vehicle/saved-list';

export const metadata: Metadata = {
  title: 'Saved cars',
  description: 'The cars you have saved in this browser.',
  robots: { index: false, follow: false },
};

export default function SavedPage() {
  return (
    <Section>
      <SectionHeading as="h1"
        eyebrow="Saved"
        title="Your shortlist"
        description="Saved cars are kept in this browser, so they survive a refresh without an account. Sign in later and the list comes with you."
      />
      <div className="mt-10">
        <SavedList />
      </div>
    </Section>
  );
}
