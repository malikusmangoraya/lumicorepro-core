import type { Metadata } from 'next';
import { CheckCircle2 } from 'lucide-react';
import { Section } from '@/components/ui/section';
import { ButtonLink } from '@/components/ui/button';

export const metadata: Metadata = {
  title: 'Payment received',
  robots: { index: false, follow: false },
};

export default async function CheckoutSuccessPage({
  searchParams,
}: {
  searchParams: Promise<{ order?: string }>;
}) {
  const { order } = await searchParams;

  return (
    <Section className="max-w-2xl">
      <div className="rounded-panel border border-emerald-500/30 bg-emerald-500/5 p-8 text-center">
        <CheckCircle2 className="mx-auto size-10 text-emerald-400" aria-hidden="true" />
        <h1 className="mt-4 font-display text-2xl font-700 text-heading">Payment received</h1>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          {order ? (
            <>
              Thank you — order{' '}
              <span className="font-semibold text-heading">{order}</span> is confirmed. The card
              processor&apos;s webhook marks it paid; a specialist arranges delivery next.
            </>
          ) : (
            'Thank you — your payment was received.'
          )}
        </p>
        <p className="mt-3 text-xs leading-relaxed text-muted">
          If the order still shows as pending after a minute, the webhook did not arrive. Nothing is
          lost: the payment is on the processor side and can be reconciled from there.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <ButtonLink href="/account/orders">View your orders</ButtonLink>
          <ButtonLink href="/shop" variant="outline">
            Back to the shop
          </ButtonLink>
        </div>
      </div>
    </Section>
  );
}
