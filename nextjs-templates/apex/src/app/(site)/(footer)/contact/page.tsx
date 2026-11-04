import type { Metadata } from 'next';
import { Clock, Mail, MapPin, Phone } from 'lucide-react';
import { Section, SectionHeading } from '@/components/ui/section';
import { Panel } from '@/components/ui/card';
import { InquiryForm } from '@/components/vehicle/inquiry-form';

export const metadata: Metadata = {
  title: 'Contact',
  description: 'Talk to an Apex specialist about a car, an inspection or a sale.',
  alternates: { canonical: '/contact' },
};

export default function ContactPage() {
  return (
    <Section>
      <SectionHeading as="h1"
        eyebrow="Contact"
        title="Tell us what you are looking for"
        description="One message reaches a specialist, not a queue. We reply within one business day."
      />

      <div className="mt-10 grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
        <Panel className="p-6">
          <h2 className="font-display text-lg font-600 text-heading">Direct lines</h2>
          <ul className="mt-5 space-y-4 text-sm">
            <li className="flex items-start gap-3">
              <Mail className="mt-0.5 size-4 text-accent" aria-hidden="true" />
              <div>
                <p className="font-medium text-heading">Email</p>
                <a href="mailto:hello@apex.com" className="text-muted hover:text-heading">
                  hello@apex.com
                </a>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <Phone className="mt-0.5 size-4 text-accent" aria-hidden="true" />
              <div>
                <p className="font-medium text-heading">Phone</p>
                <a href="tel:+15550192834" className="text-muted hover:text-heading">
                  +1 (555) 019-2834
                </a>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <MapPin className="mt-0.5 size-4 text-accent" aria-hidden="true" />
              <div>
                <p className="font-medium text-heading">Workshop</p>
                <p className="text-muted">
                  750 Innovation Way, Suite 400
                  <br />
                  Los Angeles, CA 90012
                </p>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <Clock className="mt-0.5 size-4 text-accent" aria-hidden="true" />
              <div>
                <p className="font-medium text-heading">Viewing hours</p>
                <p className="text-muted">Mon–Fri 09:00–18:00 · Sat by appointment</p>
              </div>
            </li>
          </ul>

          <p className="mt-6 border-t border-line/70 pt-4 text-xs leading-relaxed text-muted">
            Viewings are by appointment so the car is on the lift and a specialist is free when you
            arrive.
          </p>
        </Panel>

        <Panel className="p-6 sm:p-8">
          <h2 className="font-display text-lg font-600 text-heading">Send a message</h2>
          <p className="mt-1 mb-6 text-sm leading-relaxed text-muted">
            Include the make, model and budget if you are looking for something specific.
          </p>
          <InquiryForm />
        </Panel>
      </div>
    </Section>
  );
}
