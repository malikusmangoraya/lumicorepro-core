import Link from 'next/link';
import { Badge } from '@/components/ui/badge';
import { Panel } from '@/components/ui/card';
import { Stars } from '@/components/ui/stars';
import { ReviewModeration } from '@/components/admin/review-moderation';
import { prisma } from '@/lib/prisma';
import { formatDate } from '@/lib/utils';
import type { Prisma } from '@prisma/client';

export const dynamic = 'force-dynamic';

const STATUSES = ['pending', 'approved', 'rejected'] as const;

export default async function AdminReviewsPage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string }>;
}) {
  const { status } = await searchParams;
  const filter = STATUSES.includes(status as (typeof STATUSES)[number])
    ? (status as (typeof STATUSES)[number])
    : 'pending';

  let reviews: Prisma.ReviewGetPayload<{
    include: { vehicle: { select: { slug: true; title: true } } };
  }>[] = [];
  let ready = true;

  try {
    reviews = await prisma.review.findMany({
      where: { status: filter },
      orderBy: { createdAt: 'desc' },
      take: 100,
      include: { vehicle: { select: { slug: true, title: true } } },
    });
  } catch {
    ready = false;
  }

  return (
    <div className="space-y-5">
      <div>
        <h2 className="font-display text-xl font-700 text-heading">Reviews</h2>
        <p className="mt-1 text-sm text-muted">
          Nothing is published until it is approved here. Verified purchase means the same email has
          an order for that car.
        </p>
      </div>

      <nav aria-label="Filter reviews">
        <ul className="flex flex-wrap gap-1">
          {STATUSES.map((option) => (
            <li key={option}>
              <Link
                href={`/admin/reviews?status=${option}`}
                className={`inline-flex rounded-control px-3 py-1.5 text-xs font-medium capitalize ${
                  filter === option ? 'bg-primary/15 text-accent' : 'text-body/75 hover:bg-white/5'
                }`}
              >
                {option}
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      {!ready ? (
        <Panel className="p-6 text-sm text-muted">
          The database is not initialised. Run{' '}
          <code className="rounded bg-canvas px-1.5 py-0.5">npm run db:setup</code>.
        </Panel>
      ) : reviews.length === 0 ? (
        <Panel className="p-10 text-center">
          <p className="font-600 text-heading">No {filter} reviews</p>
          <p className="mx-auto mt-2 max-w-sm text-sm text-muted">
            Reviews arrive from each vehicle page and wait here for approval.
          </p>
        </Panel>
      ) : (
        <div className="space-y-3">
          {reviews.map((review) => (
            <Panel key={review.id} className="p-5">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <Stars rating={review.rating} />
                    <span className="text-sm font-medium text-heading">{review.authorName}</span>
                    {review.verifiedPurchase && <Badge tone="success">Verified</Badge>}
                    <span className="text-xs text-muted">{formatDate(review.createdAt)}</span>
                  </div>
                  <p className="mt-1 text-xs text-muted">{review.authorEmail}</p>
                  {review.vehicle && (
                    <Link
                      href={`/inventory/${review.vehicle.slug}`}
                      className="mt-1 inline-block text-xs text-accent hover:underline"
                    >
                      {review.vehicle.title}
                    </Link>
                  )}
                  {review.title && <p className="mt-2 font-medium text-heading">{review.title}</p>}
                  <p className="mt-1 whitespace-pre-line text-sm leading-relaxed text-body/85">
                    {review.comment}
                  </p>
                </div>
                <ReviewModeration id={review.id} status={review.status} />
              </div>
            </Panel>
          ))}
        </div>
      )}
    </div>
  );
}
