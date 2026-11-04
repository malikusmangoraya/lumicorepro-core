'use client';

import Image from 'next/image';
import { useCallback, useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight, Expand, X } from 'lucide-react';
import type { VehicleMedia } from '@/lib/vehicles';

export function VehicleGallery({ media, title }: { media: VehicleMedia[]; title: string }) {
  const [active, setActive] = useState(0);
  const [open, setOpen] = useState(false);

  const move = useCallback(
    (delta: number) => {
      setActive((current) => (current + delta + media.length) % media.length);
    },
    [media.length],
  );

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
      if (event.key === 'ArrowRight') move(1);
      if (event.key === 'ArrowLeft') move(-1);
    };
    document.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
    };
  }, [open, move]);

  if (media.length === 0) {
    return (
      <div className="flex aspect-[16/10] items-center justify-center rounded-panel border border-dashed border-line text-sm text-muted">
        Photos are being prepared
      </div>
    );
  }

  const current = media[active] ?? media[0];

  return (
    <>
      <div className="space-y-3">
        <div className="group relative aspect-[16/10] overflow-hidden rounded-panel border border-line bg-canvas">
          <Image
            src={current.url}
            alt={current.alt || title}
            fill
            priority
            sizes="(max-width: 1024px) 100vw, 60vw"
            className="object-cover"
          />
          <button
            type="button"
            onClick={() => setOpen(true)}
            aria-label="Open photo full screen"
            className="absolute bottom-3 right-3 inline-flex items-center gap-1.5 rounded-full border border-white/15 bg-canvas/80 px-3 py-1.5 text-xs font-medium text-heading backdrop-blur transition-colors hover:border-primary/60"
          >
            <Expand className="size-3.5" aria-hidden="true" />
            View full size
          </button>
          {media.length > 1 && (
            <>
              <button
                type="button"
                onClick={() => move(-1)}
                aria-label="Previous photo"
                className="absolute left-3 top-1/2 inline-flex size-9 -translate-y-1/2 items-center justify-center rounded-full border border-white/15 bg-canvas/75 text-heading opacity-0 backdrop-blur transition-opacity focus-visible:opacity-100 group-hover:opacity-100"
              >
                <ChevronLeft className="size-4" aria-hidden="true" />
              </button>
              <button
                type="button"
                onClick={() => move(1)}
                aria-label="Next photo"
                className="absolute right-3 top-1/2 inline-flex size-9 -translate-y-1/2 items-center justify-center rounded-full border border-white/15 bg-canvas/75 text-heading opacity-0 backdrop-blur transition-opacity focus-visible:opacity-100 group-hover:opacity-100"
              >
                <ChevronRight className="size-4" aria-hidden="true" />
              </button>
            </>
          )}
        </div>

        {media.length > 1 && (
          <ul className="flex gap-2 overflow-x-auto pb-1" aria-label="Vehicle photos">
            {media.map((image, index) => (
              <li key={image.url}>
                <button
                  type="button"
                  onClick={() => setActive(index)}
                  aria-label={`Show photo ${index + 1} of ${media.length}`}
                  aria-current={index === active}
                  className={
                    index === active
                      ? 'relative block size-20 overflow-hidden rounded-lg border-2 border-primary'
                      : 'relative block size-20 overflow-hidden rounded-lg border border-line opacity-70 transition-opacity hover:opacity-100'
                  }
                >
                  <Image
                    src={image.url}
                    alt={image.alt || `${title} photo ${index + 1}`}
                    fill
                    sizes="80px"
                    className="object-cover"
                  />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {open && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label={`${title} — full screen photo`}
          className="fixed inset-0 z-[90] flex flex-col bg-canvas/97 backdrop-blur"
        >
          <div className="flex items-center justify-between px-4 py-3">
            <p className="text-sm text-muted">
              {active + 1} / {media.length}
            </p>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Close full screen photo"
              autoFocus
              className="inline-flex size-10 items-center justify-center rounded-full border border-line text-heading transition-colors hover:border-primary/60"
            >
              <X className="size-5" aria-hidden="true" />
            </button>
          </div>
          <div className="relative flex-1">
            <Image
              src={current.url}
              alt={current.alt || title}
              fill
              sizes="100vw"
              className="object-contain"
            />
          </div>
          {media.length > 1 && (
            <div className="flex items-center justify-center gap-4 py-4">
              <button
                type="button"
                onClick={() => move(-1)}
                aria-label="Previous photo"
                className="inline-flex size-10 items-center justify-center rounded-full border border-line text-heading transition-colors hover:border-primary/60"
              >
                <ChevronLeft className="size-5" aria-hidden="true" />
              </button>
              <button
                type="button"
                onClick={() => move(1)}
                aria-label="Next photo"
                className="inline-flex size-10 items-center justify-center rounded-full border border-line text-heading transition-colors hover:border-primary/60"
              >
                <ChevronRight className="size-5" aria-hidden="true" />
              </button>
            </div>
          )}
        </div>
      )}
    </>
  );
}
