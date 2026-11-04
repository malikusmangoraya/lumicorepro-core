import type { Metadata } from 'next';
import { Section, SectionHeading } from '@/components/ui/section';
import { CartView } from '@/components/shop/cart-view';

export const metadata: Metadata = {
  title: 'Your bag',
  robots: { index: false, follow: false },
};

export default function CartPage() {
  return (
    <Section>
      <SectionHeading as="h1"
        eyebrow="Bag"
        title="Your selection"
        description="Quantities update as you go. Nothing is charged until a specialist confirms the order."
      />
      <div className="mt-10">
        <CartView />
      </div>
    </Section>
  );
}
