'use client';

import { useState } from 'react';
import { Loader2 } from 'lucide-react';
import { useSite } from '@/components/providers/site-provider';

const STATUSES = ['new', 'contacted', 'viewing_scheduled', 'closed', 'spam'] as const;

export function InquiryRowControl({
  id,
  status,
  adminNotes,
}: {
  id: string;
  status: string;
  adminNotes: string | null;
}) {
  const { notify } = useSite();
  const [current, setCurrent] = useState(status);
  const [notes, setNotes] = useState(adminNotes ?? '');
  const [pending, setPending] = useState(false);
  const [saved, setSaved] = useState(false);

  async function save(next: { status?: string; adminNotes?: string }) {
    setPending(true);
    setSaved(false);
    try {
      const response = await fetch(`/api/inquiries/${encodeURIComponent(id)}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(next),
      });
      const body = (await response.json().catch(() => ({}))) as { message?: string };
      if (!response.ok) {
        notify(body.message ?? 'Could not update the enquiry');
        return;
      }
      setSaved(true);
      notify('Enquiry updated');
    } catch {
      notify('Network error. Please try again.');
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <label htmlFor={`status-${id}`} className="sr-only">
          Enquiry status
        </label>
        <select
          id={`status-${id}`}
          value={current}
          disabled={pending}
          onChange={(event) => {
            const next = event.target.value;
            setCurrent(next);
            void save({ status: next });
          }}
          className="rounded-control border border-line bg-canvas/70 px-2 py-1.5 text-xs text-heading focus:border-primary focus:outline-none"
        >
          {STATUSES.map((option) => (
            <option key={option} value={option}>
              {option.replace('_', ' ')}
            </option>
          ))}
        </select>
        {pending && <Loader2 className="size-3.5 animate-spin text-muted" aria-hidden="true" />}
        {saved && !pending && <span className="text-xs text-emerald-400">Saved</span>}
      </div>

      <label htmlFor={`notes-${id}`} className="sr-only">
        Admin notes
      </label>
      <textarea
        id={`notes-${id}`}
        value={notes}
        onChange={(event) => setNotes(event.target.value)}
        onBlur={() => {
          if (notes !== (adminNotes ?? '')) void save({ adminNotes: notes });
        }}
        rows={2}
        placeholder="Internal notes…"
        className="w-full rounded-control border border-line bg-canvas/70 px-2 py-1.5 text-xs text-heading placeholder:text-muted/60 focus:border-primary focus:outline-none"
      />
    </div>
  );
}
