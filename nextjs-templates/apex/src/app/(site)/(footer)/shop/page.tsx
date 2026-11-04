import type { Metadata } from 'next';
import { Section, SectionHeading } from '@/components/ui/section';
import { Panel } from '@/components/ui/card';
import { ProductCard } from '@/components/shop/product-card';
import { listProducts } from '@/lib/products';

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: 'Shop',
  description: 'Care kits, driving gear and garage equipment chosen by the Apex workshop.',
  alternates: { canonical: '/shop' },
};

export default async function ShopPage() {
  const { items, ready } = await listProducts();

  return (
    <Section>
      <SectionHeading as="h1"
        eyebrow="Shop"
        title="What the workshop actually uses"
        description="A short list: the products our specialists reach for. No affiliate padding."
      />

      <div className="mt-10">
        {!ready ? (
          <Panel className="p-6 text-sm text-muted">
            The shop is unavailable right now. Run{' '}
            <code className="rounded bg-canvas px-1.5 py-0.5">npm run db:setup</code> to seed the
            store.
          </Panel>
        ) : items.length === 0 ? (
          <Panel className="p-10 text-center text-sm text-muted">No products listed yet.</Panel>
        ) : (
          <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((product) => (
              <li key={product.id}>
                <ProductCard product={product} />
              </li>
            ))}
          </ul>
        )}
      </div>
    </Section>
  );
}
