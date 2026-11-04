import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { BrandMark } from '@/components/brand/brand-mark';

/**
 * Auth shell: no site navigation and no footer. A sign-up form should be the
 * only thing on the screen, with one way back to the storefront.
 */
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative flex min-h-dvh flex-col overflow-hidden">
      <div
        className="pointer-events-none absolute inset-0 -z-10"
        aria-hidden="true"
        style={{
          background:
            'radial-gradient(60% 50% at 20% 0%, rgb(183 92 246 / 0.16), transparent 70%), radial-gradient(50% 45% at 85% 10%, rgb(226 132 252 / 0.12), transparent 72%)',
        }}
      />

      <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-6 sm:px-6">
        <Link href="/" className="flex items-center gap-2.5" aria-label="Apex Motor Collective — home">
          <BrandMark size={32} />
          <span className="flex flex-col leading-none">
            <span className="font-display text-[1.05rem] font-800 tracking-[-0.01em] text-heading">
              APEX
            </span>
            <span className="mt-0.5 text-[0.58rem] font-semibold uppercase tracking-[0.28em] text-muted">
              Motor Collective
            </span>
          </span>
        </Link>

        <Link
          href="/"
          className="inline-flex items-center gap-1.5 rounded-control border border-line px-3 py-2 text-sm font-medium text-body/80 transition-colors hover:border-primary/60 hover:text-heading"
        >
          <ArrowLeft className="size-3.5" aria-hidden="true" />
          Back to site
        </Link>
      </header>

      <main id="main" className="flex flex-1 items-center justify-center px-4 pb-16 sm:px-6">
        <div className="w-full max-w-md">{children}</div>
      </main>

      <footer className="pb-6 text-center text-xs text-muted">
        © {new Date().getFullYear()} Apex Digital ·{' '}
        <Link href="/privacy" className="hover:text-heading">
          Privacy
        </Link>{' '}
        ·{' '}
        <Link href="/terms" className="hover:text-heading">
          Terms
        </Link>
      </footer>
    </div>
  );
}
