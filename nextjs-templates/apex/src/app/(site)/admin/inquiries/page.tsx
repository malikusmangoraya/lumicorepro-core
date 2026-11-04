import Link from 'next/link';
import { Badge } from '@/components/ui/badge';
import { Panel } from '@/components/ui/card';
import { InquiryRowControl } from '@/components/admin/inquiry-row-control';
import type { Prisma } from '@prisma/client';
import { prisma } from '@/lib/prisma';
import { formatDate } from '@/lib/utils';

export const dynamic = 'force-dynamic';

const STATUSES = ['new', 'contacted', 'viewing_scheduled', 'closed', 'spam'] as const;
const TONES: Record<string, 'primary' | 'success' | 'warning' | 'danger' | 'neutral'> = {
  new: 'primary',
  contacted: 'warning',
  viewing_scheduled: 'success',
  closed: 'neutral',
  spam: 'danger',
};

export default async function AdminInquiriesPage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string }>;
}) {
  const { status } = await searchParams;
  const filter = STATUSES.includes(status as (typeof STATUSES)[number])
    ? (status as (typeof STATUSES)[number])
    : undefined;

  let inquiries: Prisma.InquiryGetPayload<{
    include: { vehicle: { select: { slug: true; title: true } } };
  }>[] = [];
  let ready = true;

  try {
    inquiries = await prisma.inquiry.findMany({
      where: filter ? { status: filter } : {},
      orderBy: { createdAt: 'desc' },
      take: 200,
      include: { vehicle: { select: { slug: true, title: true } } },
    });
  } catch {
    ready = false;
  }

  return (
    <div className="space-y-5">
      <div>
        <h2 className="font-display text-xl font-700 text-heading">Enquiries</h2>
        <p className="mt-1 text-sm text-muted">
          Change a status or leave an internal note; both save as you go.
        </p>
      </div>

      <nav aria-label="Filter by status">
        <ul className="flex flex-wrap gap-1">
          <li>
            <Link
              href="/admin/inquiries"
              className={`inline-flex rounded-control px-3 py-1.5 text-xs font-medium ${
                !filter ? 'bg-primary/15 text-accent' : 'text-body/75 hover:bg-white/5'
              }`}
            >
              All
            </Link>
          </li>
          {STATUSES.map((option) => (
            <li key={option}>
              <Link
                href={`/admin/inquiries?status=${option}`}
                className={`inline-flex rounded-control px-3 py-1.5 text-xs font-medium ${
                  filter === option ? 'bg-primary/15 text-accent' : 'text-body/75 hover:bg-white/5'
                }`}
              >
                {option.replace('_', ' ')}
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
      ) : inquiries.length === 0 ? (
        <Panel className="p-10 text-center">
          <p className="font-600 text-heading">No enquiries{filter ? ` with status “${filter}”` : ''}</p>
          <p className="mx-auto mt-2 max-w-sm text-sm text-muted">
            Enquiries arrive from the contact form and from each vehicle page.
          </p>
        </Panel>
      ) : (
        <div className="space-y-3">
          {inquiries.map((inquiry) => (
            <Panel key={inquiry.id} className="p-5">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-medium text-heading">{inquiry.name}</h3>
                    <Badge tone={TONES[inquiry.status] ?? 'neutral'}>{inquiry.status}</Badge>
                    <span className="text-xs text-muted">{formatDate(inquiry.createdAt)}</span>
                  </div>
                  <p className="mt-1 text-xs text-muted">
                    {inquiry.email}
                    {inquiry.phone ? ` · ${inquiry.phone}` : ''}
                    {inquiry.vehicle ? ' · ' : ''}
                    {inquiry.vehicle && (
                      <Link href={`/inventory/${inquiry.vehicle.slug}`} className="text-accent hover:underline">
                        {inquiry.vehicle.title}
                      </Link>
                    )}
                  </p>
                  <p className="mt-3 whitespace-pre-line text-sm leading-relaxed text-body/85">
                    {inquiry.message}
                  </p>
                </div>

                <div className="w-full sm:w-64">
                  <InquiryRowControl
                    id={inquiry.id}
                    status={inquiry.status}
                    adminNotes={inquiry.adminNotes}
                  />
                </div>
              </div>
            </Panel>
          ))}
        </div>
      )}
    </div>
  );
}
