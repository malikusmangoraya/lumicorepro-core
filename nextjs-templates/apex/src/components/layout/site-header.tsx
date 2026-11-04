import Link from 'next/link';
import { BrandLockup } from '@/components/brand/brand-mark';
import { SessionMenu } from '@/components/layout/session-menu';

const links = [
  { href: '/inventory', label: 'Inventory' },
  { href: '/services', label: 'Services' },
  { href: '/pricing', label: 'Pricing' },
  { href: '/about', label: 'About' },
  { href: '/contact', label: 'Contact' },
];

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-line/70 bg-canvas/85 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-6 px-4 sm:px-6">
        <BrandLockup />

        <nav aria-label="Primary" className="hidden items-center gap-1 md:flex">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="rounded-lg px-3 py-2 text-sm font-medium text-body/80 transition-colors hover:bg-white/5 hover:text-heading"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <SessionMenu />
      </div>

      <nav aria-label="Primary mobile" className="border-t border-line/50 md:hidden">
        <ul className="mx-auto flex max-w-6xl items-center gap-1 overflow-x-auto px-2 py-2 text-sm">
          {links.map((link) => (
            <li key={link.href}>
              <Link
                href={link.href}
                className="whitespace-nowrap rounded-lg px-3 py-1.5 font-medium text-body/80 transition-colors hover:bg-white/5 hover:text-heading"
              >
                {link.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </header>
  );
}
