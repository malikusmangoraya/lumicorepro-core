import { Badge } from '@/components/ui/badge';
import { Stars } from '@/components/ui/stars';
import { ReviewForm } from '@/components/vehicle/review-form';
import { prisma } from '@/lib/prisma';
import { formatDate } from '@/lib/utils';

type Target = {
  kind: 'vehicle' | 'product';
  id: string;
  slug: string;
};

/** Approved reviews plus the form, for either a vehicle or a shop product. */
export async function ReviewsSection({ target }: { target: Target }) {
  const where = {
    status: 'approved',
    ...(target.kind === 'vehicle' ? { vehicleId: target.id } : { productId: target.id }),
  };

  let reviews: {
    id: string;
    authorName: string;
    rating: number;
    title: string | null;
    comment: string;
    verifiedPurchase: boolean;
    createdAt: Date;
  }[] = [];
  let average: number | null = null;

  try {
    const [rows, aggregate] = await Promise.all([
      prisma.review.findMany({
        where,
        orderBy: { createdAt: 'desc' },
        take: 20,
        select: {
          id: true,
          authorName: true,
          rating: true,
          title: true,
          comment: true,
          verifiedPurchase: true,
          createdAt: true,
        },
      }),
      prisma.review.aggregate({ where, _avg: { rating: true } }),
    ]);
    reviews = rows;
    average = aggregate._avg.rating ? Math.round(aggregate._avg.rating * 10) / 10 : null;
  } catch {
    // Reviews are additive; a database hiccup must not take the page down.
  }

  return (
    <section aria-labelledby="reviews-heading" className="mt-8">
      <div className="flex flex-wrap items-center gap-3">
        <h2 id="reviews-heading" className="font-display text-lg font-600 text-heading">
          Reviews
        </h2>
        {average !== null ? (
          <span className="flex items-center gap-2 text-sm text-muted">
            <Stars rating={average} />
            {average} · {reviews.length} review{reviews.length === 1 ? '' : 's'}
          </span>
        ) : (
          <span className="text-sm text-muted">No reviews yet</span>
        )}
      </div>

      {reviews.length > 0 && (
        <ul className="mt-4 space-y-3">
          {reviews.map((review) => (
            <li key={review.id} className="rounded-panel border border-line bg-surface/50 p-5">
              <div className="flex flex-wrap items-center gap-2">
                <Stars rating={review.rating} />
                <span className="text-sm font-medium text-heading">{review.authorName}</span>
                {review.verifiedPurchase && <Badge tone="success">Verified purchase</Badge>}
                <span className="text-xs text-muted">{formatDate(review.createdAt)}</span>
              </div>
              {review.title && <p className="mt-2 font-medium text-heading">{review.title}</p>}
              <p className="mt-1 whitespace-pre-line text-sm leading-relaxed text-body/85">
                {review.comment}
              </p>
            </li>
          ))}
        </ul>
      )}

      <div className="mt-5">
        <ReviewForm
          {...(target.kind === 'vehicle'
            ? { vehicleSlug: target.slug }
            : { productSlug: target.slug })}
        />
      </div>
    </section>
  );
}
