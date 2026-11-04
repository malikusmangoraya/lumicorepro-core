'use client';

import { useRef, useState } from 'react';
import { ImagePlus, Loader2 } from 'lucide-react';
import { useSite } from '@/components/providers/site-provider';

/**
 * Uploads images straight into the database (see /api/uploads) and hands the
 * resulting URLs back to the form. No file is written to disk: on a serverless
 * host a file in public/ disappears with the next deploy.
 */
export function ImageUploader({ onUploaded }: { onUploaded: (url: string) => void }) {
  const { notify } = useSite();
  const inputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);

  async function upload(files: FileList) {
    setBusy(true);
    let uploaded = 0;

    for (const file of Array.from(files)) {
      const body = new FormData();
      body.append('file', file);
      try {
        const response = await fetch('/api/uploads', { method: 'POST', body });
        const payload = (await response.json().catch(() => ({}))) as {
          success?: boolean;
          message?: string;
          data?: { url?: string };
        };
        if (!response.ok || !payload.success || !payload.data?.url) {
          notify(payload.message ?? `Could not upload ${file.name}`);
          continue;
        }
        onUploaded(payload.data.url);
        uploaded += 1;
      } catch {
        notify(`Network error uploading ${file.name}`);
      }
    }

    setBusy(false);
    if (uploaded > 0) notify(`${uploaded} image${uploaded === 1 ? '' : 's'} uploaded`);
    if (inputRef.current) inputRef.current.value = '';
  }

  return (
    <div className="rounded-control border border-dashed border-line bg-canvas/40 p-4">
      <input
        ref={inputRef}
        id="media-upload"
        type="file"
        accept="image/jpeg,image/png,image/webp,image/avif"
        multiple
        className="sr-only"
        onChange={(event) => {
          if (event.target.files?.length) void upload(event.target.files);
        }}
      />
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-heading">Upload photos</p>
          <p className="mt-0.5 text-xs text-muted">
            JPEG, PNG, WebP or AVIF · 3 MB each. The URL is added below.
          </p>
        </div>
        <button
          type="button"
          disabled={busy}
          onClick={() => inputRef.current?.click()}
          className="inline-flex items-center gap-2 rounded-control border border-line px-3 py-2 text-sm font-semibold text-heading transition-colors hover:border-primary/60 hover:bg-white/5 disabled:opacity-60"
        >
          {busy ? (
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
          ) : (
            <ImagePlus className="size-4" aria-hidden="true" />
          )}
          {busy ? 'Uploading…' : 'Choose images'}
        </button>
      </div>
    </div>
  );
}
