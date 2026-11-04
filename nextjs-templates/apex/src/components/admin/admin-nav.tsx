'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Car, LayoutDashboard, Mail, MessageSquare, Package } from 'lucide-react';
import { cn } from '@/lib/utils';

const TABS = [
  { href: '/admin', label: 'Overview', icon: LayoutDashboard },
  { href: '/admin/vehicles', label: 'Vehicles', icon: Car },
  { href: '/admin/orders', label: 'Orders', icon: Package },
  { href: '/admin/inquiries', label: 'Enquiries', icon: MessageSquare },
  { href: '/admin/newsletter', label: 'Newsletter', icon: Mail },
];

export function AdminNav() {
  const pathname = usePathname();

  return (
    <nav aria-label="Admin sections" className="mt-5">
      <ul className="flex flex-wrap gap-1">
        {TABS.map((tab) => {
          const active =
            tab.href === '/admin' ? pathname === '/admin' : pathname.startsWith(tab.href);
          return (
            <li key={tab.href}>
              <Link
                href={tab.href}
                aria-current={active ? 'page' : undefined}
                className={cn(
                  'inline-flex items-center gap-2 rounded-control px-3.5 py-2 text-sm font-medium transition-colors',
                  active
                    ? 'bg-primary/15 text-accent'
                    : 'text-body/75 hover:bg-white/5 hover:text-heading',
                )}
              >
                <tab.icon className="size-4" aria-hidden="true" />
                {tab.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
