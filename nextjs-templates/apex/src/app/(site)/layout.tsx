import { SiteHeader } from '@/components/layout/site-header';
import { SiteFooter } from '@/components/layout/site-footer';
import { SiteProvider } from '@/components/providers/site-provider';
import { BackToTop } from '@/components/ui/back-to-top';
import { PromoBanner } from '@/components/layout/promo-banner';
import { ContactFloat } from '@/components/layout/contact-float';
import { ConsentBanner } from '@/components/consent/consent-banner';

export default function SiteLayout({ children }: { children: React.ReactNode }) {
  return (
    <SiteProvider>
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <PromoBanner />
      <SiteHeader />
      <main id="main" className="min-h-[60dvh]">
        {children}
      </main>
      <SiteFooter />
      <ContactFloat />
      <BackToTop />
      <ConsentBanner />
    </SiteProvider>
  );
}
