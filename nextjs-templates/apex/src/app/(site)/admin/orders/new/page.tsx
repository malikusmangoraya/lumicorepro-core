import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { OrderCreateForm } from '@/components/admin/order-create-form';
import { prisma } from '@/lib/prisma';
import { formatCurrency } from '@/lib/utils';

export const dynamic = 'force-dynamic';

export default async function NewOrderPage() {
  let vehicles: { slug: string; label: string; price: number; currency: string }[] = [];
  let products: { slug: string; label: string; price: number; currency: string }[] = [];

  try {
    const [vehicleRows, productRows] = await Promise.all([
      prisma.vehicle.findMany({
        where: { status: { in: ['active', 'reserved'] } },
        orderBy: { title: 'asc' },
        select: { slug: true, title: true, price: true, currency: true },
      }),
      prisma.product.findMany({
        where: { isActive: true },
        orderBy: { title: 'asc' },
        select: { slug: true, title: true, price: true },
      }),
    ]);
    vehicles = vehicleRows.map((row) => ({
      slug: row.slug,
      label: row.title,
      price: row.price,
      currency: row.currency,
    }));
    products = productRows.map((row) => ({
      slug: row.slug,
      label: row.title,
      price: row.price,
      currency: 'USD',
    }));
  } catch {
    // The form renders an empty-state when the database is unavailable.
  }

  return (
    <div className="space-y-5">
      <div>
        <Link
          href="/admin/orders"
          className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-heading"
        >
          <ArrowLeft className="size-4" aria-hidden="true" />
          Back to orders
        </Link>
        <h2 className="mt-3 font-display text-xl font-700 text-heading">New order</h2>
        <p className="mt-1 text-sm text-muted">
          For a phone or in-person sale. The order starts as pending; mark it paid once the money
          lands. Totals are recomputed on the server.
        </p>
      </div>

      <OrderCreateForm vehicles={vehicles} products={products} />

      <p className="text-xs text-muted">
        Example: {vehicles[0] ? formatCurrency(vehicles[0].price, vehicles[0].currency) : '—'} for
        the first listed car.
      </p>
    </div>
  );
}
