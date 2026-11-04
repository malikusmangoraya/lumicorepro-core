import Link from 'next/link';
import { ButtonLink } from '@/components/ui/button';

export default function NotFound() {
  return (
    <section className="mx-auto flex max-w-3xl flex-col items-center px-4 py-28 text-center sm:px-6">
      <p className="font-display text-[7rem] font-800 leading-none text-primary/20 sm:text-[10rem]">
        404
      </p>
      <h1 className="-mt-4 text-balance font-display text-3xl font-700 text-heading sm:text-4xl">
        That road does not exist
      </h1>
      <p className="mt-4 max-w-md text-pretty text-sm leading-relaxed text-muted">
        The page you asked for has been moved or never existed. The inventory is the best place to
        start again.
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
    </section>
  );
}
