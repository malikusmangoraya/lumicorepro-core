import { Panel } from '@/components/ui/card';
import { SubscriberToggle } from '@/components/admin/subscriber-toggle';
import type { Prisma } from '@prisma/client';
import { prisma } from '@/lib/prisma';
import { formatDate } from '@/lib/utils';

export const dynamic = 'force-dynamic';

export default async function AdminNewsletterPage() {
  let subscribers: Prisma.NewsletterSubscriberGetPayload<Record<string, never>>[] = [];
  let ready = true;

  try {
    subscribers = await prisma.newsletterSubscriber.findMany({
      orderBy: { createdAt: 'desc' },
      take: 200,
    });
  } catch {
    ready = false;
  }

  const active = subscribers.filter((subscriber) => subscriber.isActive).length;

  return (
    <div className="space-y-5">
      <div>
        <h2 className="font-display text-xl font-700 text-heading">Newsletter</h2>
        <p className="mt-1 text-sm text-muted">
          {subscribers.length} subscriber{subscribers.length === 1 ? '' : 's'} · {active} active.
          The form lives in the footer of the storefront.
        </p>
      </div>

      {!ready ? (
        <Panel className="p-6 text-sm text-muted">
          The database is not initialised. Run{' '}
          <code className="rounded bg-canvas px-1.5 py-0.5">npm run db:setup</code>.
        </Panel>
      ) : subscribers.length === 0 ? (
        <Panel className="p-10 text-center">
          <p className="font-600 text-heading">No subscribers yet</p>
          <p className="mx-auto mt-2 max-w-sm text-sm text-muted">
            Sign-ups from the storefront footer appear here.
          </p>
        </Panel>
      ) : (
        <Panel className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[520px] text-left text-sm">
              <thead className="text-xs uppercase tracking-wide text-muted">
                <tr className="border-b border-line/70">
                  <th scope="col" className="px-5 py-3 font-medium">Email</th>
                  <th scope="col" className="px-5 py-3 font-medium">Source</th>
                  <th scope="col" className="px-5 py-3 font-medium">Joined</th>
                  <th scope="col" className="px-5 py-3 text-right font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line/50">
                {subscribers.map((subscriber) => (
                  <tr key={subscriber.id}>
                    <td className="px-5 py-3 text-heading">{subscriber.email}</td>
                    <td className="px-5 py-3 text-muted">{subscriber.source}</td>
                    <td className="px-5 py-3 text-muted">{formatDate(subscriber.createdAt)}</td>
                    <td className="px-5 py-3 text-right">
                      <SubscriberToggle id={subscriber.id} isActive={subscriber.isActive} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}
    </div>
  );
}
