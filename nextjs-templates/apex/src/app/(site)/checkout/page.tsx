import type { Metadata } from 'next';
import { Section, SectionHeading } from '@/components/ui/section';
import { CheckoutForm } from '@/components/shop/checkout-form';

export const metadata: Metadata = {
  title: 'Checkout',
  robots: { index: false, follow: false },
};

export default function CheckoutPage() {
  return (
    <Section>
      <SectionHeading as="h1"
        eyebrow="Checkout"
        title="Where should it go?"
        description="We record the order and a specialist confirms stock, shipping and payment with you."
      />
      <div className="mt-10">
        <CheckoutForm />
      </div>
    </Section>
  );
}
