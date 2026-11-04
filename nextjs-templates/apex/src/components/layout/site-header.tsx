import { BrandLockup } from '@/components/brand/brand-mark';
import { SessionMenu } from '@/components/layout/session-menu';
import { NavLinks } from '@/components/layout/nav-links';
import { TrayLinks } from '@/components/layout/tray-links';

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-line/70 bg-canvas/85 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-6 px-4 sm:px-6">
        <BrandLockup />

        <nav aria-label="Primary" className="hidden items-center gap-1 md:flex">
          <NavLinks variant="desktop" />
        </nav>

        <div className="flex items-center gap-1">
          <TrayLinks />
          <SessionMenu />
        </div>
      </div>

      <nav aria-label="Primary mobile" className="border-t border-line/50 md:hidden">
        <NavLinks variant="mobile" />
      </nav>
    </header>
  );
}
