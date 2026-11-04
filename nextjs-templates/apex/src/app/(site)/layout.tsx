import { SiteHeader } from '@/components/layout/site-header';
import { SiteProvider } from '@/components/providers/site-provider';
import { BackToTop } from '@/components/ui/back-to-top';
import { PromoBanner } from '@/components/layout/promo-banner';
import { ContactFloat } from '@/components/layout/contact-float';
import { ConsentBanner } from '@/components/consent/consent-banner';
import { ChatWidget } from '@/components/layout/chat-widget';
import { ServiceWorkerRegistrar } from '@/components/pwa/service-worker-registrar';

/**
 * Site chrome without the footer.
 *
 * The footer is a page of exits: fourteen links plus a newsletter form. That is
 * right for marketing and account pages and wrong for a cart, a checkout or the
 * admin control room, where the visitor has one task to finish. Those routes
 * live directly under this layout; everything that wants a footer sits in the
 * `(footer)` group whose own layout adds it.
 */
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
      <ContactFloat />
      <BackToTop />
      <ConsentBanner />
      <ChatWidget />
      <ServiceWorkerRegistrar />
    </SiteProvider>
  );
}
