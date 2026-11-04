import Link from 'next/link';
import { ButtonLink } from '@/components/ui/button';
import { BrandLockup } from '@/components/brand/brand-mark';

export default function NotFound() {
  return (
    <div className="relative flex min-h-dvh flex-col">
      <div
        className="pointer-events-none absolute inset-0 -z-10"
        aria-hidden="true"
        style={{
          background:
            'radial-gradient(55% 45% at 50% 0%, rgb(183 92 246 / 0.14), transparent 70%)',
        }}
      />

      <header className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6">
        <BrandLockup />
      </header>

      <main className="mx-auto flex flex-1 flex-col items-center justify-center px-4 pb-20 text-center sm:px-6">
        <p className="font-display text-[7rem] font-800 leading-none text-primary/20 sm:text-[10rem]">
          404
        </p>
        <h1 className="-mt-4 text-balance font-display text-3xl font-700 text-heading sm:text-4xl">
          That road does not exist
        </h1>
        <p className="mt-4 max-w-md text-pretty text-sm leading-relaxed text-muted">
          The page you asked for has been moved or never existed. The inventory is the best place
          to start again.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <ButtonLink href="/inventory">Browse inventory</ButtonLink>
          <ButtonLink href="/" variant="outline">
            Back home
          </ButtonLink>
        </div>
        <p className="mt-8 text-xs text-muted">
          Looking for something specific?{' '}
          <Link href="/contact" className="text-accent hover:underline">
            Ask a specialist
          </Link>
          .
        </p>
      </main>
    </div>
  );
}
