import type { Metadata } from 'next';
import Link from 'next/link';
import { redirect } from 'next/navigation';
import { RegisterForm } from '@/components/auth/auth-forms';
import { getSession } from '@/lib/auth';

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: 'Create account',
  robots: { index: false, follow: false },
};

export default async function RegisterPage() {
  const session = await getSession().catch(() => null);
  if (session) redirect('/account');

  return (
    <div>
      <p className="section-eyebrow">Create account</p>
      <h1 className="mt-3 font-display text-3xl font-700 text-heading">Join the collective</h1>
      <p className="mt-2 text-sm leading-relaxed text-muted">
        Save cars, keep every enquiry in one place, and manage your membership.
      </p>

      <div className="mt-7 rounded-panel border border-line bg-surface/70 p-6 shadow-panel backdrop-blur">
        <RegisterForm />
      </div>

      <p className="mt-5 text-sm text-muted">
        Already registered?{' '}
        <Link href="/login" className="font-medium text-accent hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}
