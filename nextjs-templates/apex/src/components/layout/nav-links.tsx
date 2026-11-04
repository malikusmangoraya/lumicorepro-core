'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { useSite } from '@/components/providers/site-provider';
import type { MessageKey } from '@/lib/i18n/dictionaries';

export const NAV_LINKS: { href: string; key: MessageKey }[] = [
  { href: '/', key: 'nav.home' },
  { href: '/inventory', key: 'nav.inventory' },
  { href: '/shop', key: 'nav.shop' },
  { href: '/services', key: 'nav.services' },
  { href: '/pricing', key: 'nav.pricing' },
  { href: '/about', key: 'nav.about' },
  { href: '/contact', key: 'nav.contact' },
];

function isActive(pathname: string, href: string) {
  if (href === '/') return pathname === '/';
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function NavLinks({ variant }: { variant: 'desktop' | 'mobile' }) {
  const pathname = usePathname();
  const { t } = useSite();

  // The mobile row wraps instead of scrolling: a horizontally scrolled row
  // hides the last link with no affordance, which is how a visitor loses their
  // way back to the home page.
  if (variant === 'mobile') {
    return (
      <ul className="mx-auto flex max-w-6xl flex-wrap items-center gap-1 px-2 py-2 text-sm">
        {NAV_LINKS.map((link) => {
          const active = isActive(pathname, link.href);
          return (
            <li key={link.href}>
              <Link
                href={link.href}
                aria-current={active ? 'page' : undefined}
                className={cn(
                  'inline-flex whitespace-nowrap rounded-lg px-2.5 py-1.5 font-medium transition-colors',
                  active
                    ? 'bg-primary/15 text-accent'
                    : 'text-body/80 hover:bg-white/5 hover:text-heading',
                )}
              >
                {t(link.key)}
              </Link>
            </li>
          );
        })}
      </ul>
    );
  }

  return (
    <>
      {NAV_LINKS.map((link) => {
        const active = isActive(pathname, link.href);
        return (
          <Link
            key={link.href}
            href={link.href}
            aria-current={active ? 'page' : undefined}
            className={cn(
              'rounded-lg px-3 py-2 text-sm font-medium transition-colors',
              active ? 'bg-white/5 text-heading' : 'text-body/80 hover:bg-white/5 hover:text-heading',
            )}
          >
            {t(link.key)}
          </Link>
        );
      })}
    </>
  );
}
