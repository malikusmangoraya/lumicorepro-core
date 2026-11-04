import Link from 'next/link';
import { BrandMark } from '@/components/brand/brand-mark';
import { NewsletterForm } from '@/components/layout/newsletter-form';

const columns = [
  {
    title: 'Inventory',
    links: [
      { href: '/inventory', label: 'All vehicles' },
      { href: '/inventory?make=Porsche', label: 'Porsche' },
      { href: '/inventory?make=Ferrari', label: 'Ferrari' },
      { href: '/inventory?sort=price-asc', label: 'Lowest price first' },
    ],
  },
  {
    title: 'Services',
    links: [
      { href: '/services', label: 'Pre-purchase inspection' },
      { href: '/services', label: 'Provenance research' },
      { href: '/services', label: 'Private viewings' },
      { href: '/services', label: 'Enclosed delivery' },
    ],
  },
  {
    title: 'Company',
    links: [
      { href: '/about', label: 'About Apex' },
      { href: '/insights', label: 'Market insights' },
      { href: '/pricing', label: 'Membership' },
      { href: '/contact', label: 'Contact' },
    ],
  },
  {
    title: 'Legal',
    links: [
      { href: '/privacy', label: 'Privacy policy' },
      { href: '/terms', label: 'Terms of service' },
      { href: '/login', label: 'Sign in' },
      { href: '/register', label: 'Create account' },
    ],
  },
];

export function SiteFooter() {
  return (
    <footer className="border-t border-line/70 bg-footer">
      <div className="mx-auto max-w-6xl px-4 py-14 sm:px-6">
        <div className="grid gap-10 md:grid-cols-[1.4fr_repeat(4,1fr)]">
          <div>
            <div className="flex items-center gap-2.5">
              <BrandMark size={30} />
              <span className="font-display text-lg font-700 text-heading">Apex</span>
            </div>
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-muted">
              A curated collective of performance and collector cars. Every listing is inspected,
              documented and delivered by people who drive them.
            </p>
            <p className="mt-4 text-sm text-body/70">
              <a href="mailto:hello@apex.com" className="hover:text-heading">
                hello@apex.com
              </a>
              <span aria-hidden="true"> · </span>
              <a href="tel:+15550192834" className="hover:text-heading">
                +1 (555) 019-2834
              </a>
            </p>

            <div className="mt-6 max-w-xs">
              <NewsletterForm />
            </div>
          </div>

          {columns.map((column) => (
            <nav key={column.title} aria-label={column.title}>
              <h2 className="text-xs font-semibold uppercase tracking-[0.18em] text-heading">
                {column.title}
              </h2>
              <ul className="mt-4 space-y-2.5">
                {column.links.map((link) => (
                  <li key={`${link.href}-${link.label}`}>
                    <Link
                      href={link.href}
                      className="text-sm text-muted transition-colors hover:text-heading"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          ))}
        </div>

        <div className="mt-12 flex flex-col gap-3 border-t border-line/60 pt-6 text-xs text-muted sm:flex-row sm:items-center sm:justify-between">
          <p>© {new Date().getFullYear()} Apex Digital. All rights reserved.</p>
          <p>Prices shown in each listing&apos;s own currency. No conversion applied.</p>
        </div>
      </div>
    </footer>
  );
}
