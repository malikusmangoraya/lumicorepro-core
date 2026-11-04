'use client';

import { useState } from 'react';
import { Link2, Share2 } from 'lucide-react';
import { useSite } from '@/components/providers/site-provider';

export function ShareButton({ title, url }: { title: string; url: string }) {
  const { notify } = useSite();
  const [copied, setCopied] = useState(false);

  const onClick = async () => {
    const shareData = { title, text: `${title} — Apex Motor Collective`, url };

    if (typeof navigator !== 'undefined' && navigator.share) {
      try {
        await navigator.share(shareData);
        return;
      } catch {
        // The visitor dismissed the sheet, or the platform refused it.
      }
    }

    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      notify('Link copied to clipboard');
    } catch {
      notify('Could not copy the link. Copy it from the address bar.');
    }
  };

  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex h-11 items-center justify-center gap-2 rounded-control border border-line px-4 text-sm font-semibold text-heading transition-colors hover:border-primary/60 hover:bg-white/5"
    >
      {copied ? (
        <Link2 className="size-4 text-accent" aria-hidden="true" />
      ) : (
        <Share2 className="size-4" aria-hidden="true" />
      )}
      {copied ? 'Copied' : 'Share'}
    </button>
  );
}
