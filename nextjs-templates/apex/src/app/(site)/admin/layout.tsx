import type { Metadata } from 'next';
import { redirect } from 'next/navigation';
import { getSession } from '@/lib/auth';
import { AdminNav } from '@/components/admin/admin-nav';

export const metadata: Metadata = {
  title: 'Admin',
  robots: { index: false, follow: false },
};

export const dynamic = 'force-dynamic';

export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const session = await getSession().catch(() => null);
  if (!session) redirect('/login?next=/admin');
  if (session.role !== 'admin') redirect('/account');

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-10 sm:px-6">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-line/70 pb-5">
        <div>
          <p className="section-eyebrow">Control room</p>
          <h1 className="mt-2 font-display text-2xl font-700 text-heading sm:text-3xl">
            Apex operations
          </h1>
        </div>
        <p className="text-xs text-muted">Signed in as {session.email}</p>
      </div>

      <AdminNav />

      <div className="mt-8">{children}</div>
    </div>
  );
}
