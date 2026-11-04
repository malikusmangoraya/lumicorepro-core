import type { Metadata } from 'next';
import { redirect } from 'next/navigation';
import { Section, SectionHeading } from '@/components/ui/section';
import { Panel } from '@/components/ui/card';
import { SignOutButton } from '@/components/auth/auth-forms';
import { DeleteAccountButton } from '@/components/auth/delete-account-button';
import { getSession } from '@/lib/auth';
import { prisma } from '@/lib/prisma';
import { formatDate } from '@/lib/utils';

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: 'Account',
  robots: { index: false, follow: false },
};

async function loadAccount(userId: string) {
  try {
    const [user, inquiries] = await Promise.all([
      prisma.user.findUnique({
        where: { id: userId },
        select: { name: true, email: true, role: true, createdAt: true },
      }),
      prisma.inquiry.findMany({
        where: { userId },
        orderBy: { createdAt: 'desc' },
        take: 5,
        select: { id: true, status: true, createdAt: true, message: true },
      }),
    ]);
    return { user, inquiries, ready: true };
  } catch {
    return { user: null, inquiries: [], ready: false };
  }
}

export default async function AccountPage() {
  const session = await getSession().catch(() => null);
  if (!session) redirect('/login?next=/account');

  const { user, inquiries, ready } = await loadAccount(session.id);

  return (
    <Section>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <SectionHeading as="h1"
          eyebrow="Account"
          title={user?.name ? `Hello, ${user.name.split(' ')[0]}` : 'Your account'}
          description="Your details, your enquiries, and the controls for exporting or deleting everything we hold."
        />
        <SignOutButton />
      </div>

      <div className="mt-10 grid gap-5 lg:grid-cols-2">
        <Panel className="p-6">
          <h2 className="font-display text-lg font-600 text-heading">Details</h2>
          <dl className="mt-4 space-y-3 text-sm">
            <div className="flex justify-between gap-4 border-b border-line/60 pb-3">
              <dt className="text-muted">Email</dt>
              <dd className="text-heading">{user?.email ?? session.email}</dd>
            </div>
            <div className="flex justify-between gap-4 border-b border-line/60 pb-3">
              <dt className="text-muted">Role</dt>
              <dd className="text-heading">{user?.role ?? session.role}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-muted">Member since</dt>
              <dd className="text-heading">{user ? formatDate(user.createdAt) : '—'}</dd>
            </div>
          </dl>
          {!ready && (
            <p className="mt-4 text-xs text-amber-300">
              The database is not initialised, so account details cannot be read. Run{' '}
              <code className="rounded bg-canvas px-1.5 py-0.5">npm run db:setup</code>.
            </p>
          )}
        </Panel>

        <Panel className="p-6">
          <h2 className="font-display text-lg font-600 text-heading">Recent enquiries</h2>
          {inquiries.length === 0 ? (
            <p className="mt-4 text-sm text-muted">No enquiries yet.</p>
          ) : (
            <ul className="mt-4 space-y-3">
              {inquiries.map((inquiry) => (
                <li key={inquiry.id} className="border-b border-line/60 pb-3 last:border-0 last:pb-0">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm text-heading">{inquiry.status}</p>
                    <p className="text-xs text-muted">{formatDate(inquiry.createdAt)}</p>
                  </div>
                  <p className="mt-1 line-clamp-2 text-xs text-muted">{inquiry.message}</p>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>

      <Panel className="mt-5 p-6">
        <h2 className="font-display text-lg font-600 text-heading">Your data</h2>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted">
          Export everything we hold about you as JSON, or delete the account. Deletion removes your
          personal data immediately; anonymised transaction records are retained for the statutory
          accounting period.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <a
            href="/api/auth/account/export"
            className="inline-flex h-9 items-center rounded-control border border-line px-3.5 text-sm font-semibold text-heading transition-colors hover:border-primary/60"
          >
            Export my data
          </a>
          <DeleteAccountButton />
        </div>
      </Panel>
    </Section>
  );
}

