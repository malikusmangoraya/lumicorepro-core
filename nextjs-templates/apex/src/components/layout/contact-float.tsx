import { MessageCircle, Phone } from 'lucide-react';
import { site } from '@/lib/site-config';

/**
 * Always-reachable contact actions. On a phone this is the difference between a
 * lead and a bounce, so it sits above the content on small screens and stays
 * out of the way on desktop.
 */
export function ContactFloat() {
  return (
    <div className="fixed bottom-4 left-4 z-40 flex flex-col gap-2">
      <a
        href={site.phoneHref}
        aria-label={`Call ${site.name} on ${site.phone}`}
        className="inline-flex size-11 items-center justify-center rounded-full border border-line bg-surface/90 text-heading shadow-lg backdrop-blur transition-colors hover:border-primary/60 hover:text-accent"
      >
        <Phone className="size-4" aria-hidden="true" />
      </a>
      {site.whatsapp && (
        <a
          href={`https://wa.me/${site.whatsapp.replace(/[^0-9]/g, '')}`}
          target="_blank"
          rel="noreferrer noopener"
          aria-label="Message us on WhatsApp"
          className="inline-flex size-11 items-center justify-center rounded-full border border-emerald-500/40 bg-emerald-500/10 text-emerald-300 shadow-lg backdrop-blur transition-colors hover:bg-emerald-500/20"
        >
          <MessageCircle className="size-4" aria-hidden="true" />
        </a>
      )}
    </div>
  );
}
