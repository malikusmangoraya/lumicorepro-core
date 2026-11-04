import { SiteHeader } from '@/components/layout/site-header';
import { SiteFooter } from '@/components/layout/site-footer';
import { SiteProvider } from '@/components/providers/site-provider';
import { BackToTop } from '@/components/ui/back-to-top';

export default function SiteLayout({ children }: { children: React.ReactNode }) {
  return (
    <SiteProvider>
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <SiteHeader />
      <main id="main" className="min-h-[60dvh]">
        {children}
      </main>
      <SiteFooter />
      <BackToTop />
    </SiteProvider>
  );
}
