import type { Metadata } from 'next';
import Link from 'next/link';
import { redirect } from 'next/navigation';
import { LoginForm } from '@/components/auth/auth-forms';
import { getSession } from '@/lib/auth';

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: 'Sign in',
  robots: { index: false, follow: false },
};

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  const session = await getSession().catch(() => null);
  if (session) redirect('/account');

  const { next } = await searchParams;
  const target = next?.startsWith('/') ? next : '/account';

  return (
    <div>
      <p className="section-eyebrow">Account</p>
      <h1 className="mt-3 font-display text-3xl font-700 text-heading">Welcome back</h1>
      <p className="mt-2 text-sm leading-relaxed text-muted">
        Sign in to track enquiries, save cars and manage your membership.
      </p>

      <div className="mt-7 rounded-panel border border-line bg-surface/70 p-6 shadow-panel backdrop-blur">
        <LoginForm next={target} />
      </div>

      <p className="mt-5 text-sm text-muted">
        No account yet?{' '}
        <Link href="/register" className="font-medium text-accent hover:underline">
          Create one
        </Link>
      </p>

      <p className="mt-3 text-xs leading-relaxed text-muted">
        Demo credentials after running{' '}
        <code className="rounded bg-canvas px-1.5 py-0.5">npm run db:seed</code>:{' '}
        <span className="text-body">admin@apex.com</span> /{' '}
        <span className="text-body">Password123!</span>
      </p>
    </div>
  );
}
