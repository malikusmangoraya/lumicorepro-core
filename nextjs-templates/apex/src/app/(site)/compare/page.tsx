import type { Metadata } from 'next';
import { Section, SectionHeading } from '@/components/ui/section';
import { CompareTable } from '@/components/vehicle/compare-table';

export const metadata: Metadata = {
  title: 'Compare cars',
  description: 'Put up to three cars side by side and compare them spec by spec.',
  robots: { index: false, follow: false },
};

export default function ComparePage() {
  return (
    <Section>
      <SectionHeading as="h1"
        eyebrow="Compare"
        title="Three cars, one table"
        description="Specs, price and provenance side by side. Remove a column to make room for another car."
      />
      <div className="mt-10">
        <CompareTable />
      </div>
    </Section>
  );
}
