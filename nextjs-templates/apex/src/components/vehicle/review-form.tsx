'use client';

import { useState } from 'react';
import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Field, Input, Textarea } from '@/components/ui/field';
import { useSite } from '@/components/providers/site-provider';

export function ReviewForm({ vehicleSlug }: { vehicleSlug: string }) {
  const { notify } = useSite();
  const [pending, setPending] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rating, setRating] = useState(5);

  if (done) {
    return (
      <div role="status" className="rounded-panel border border-emerald-500/30 bg-emerald-500/5 p-5">
        <p className="text-sm font-medium text-heading">Thank you — your review is in moderation.</p>
        <p className="mt-1 text-xs leading-relaxed text-muted">
          Reviews are published after an admin checks them, so spam never reaches this page.
        </p>
      </div>
    );
  }

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;
    setPending(true);
    setError(null);

    const form = new FormData(event.currentTarget);
    const text = (key: string) => String(form.get(key) ?? '').trim();

    try {
      const response = await fetch('/api/reviews', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vehicleSlug,
          authorName: text('authorName'),
          authorEmail: text('authorEmail'),
          rating,
          title: text('title'),
          comment: text('comment'),
        }),
      });
      const body = (await response.json().catch(() => ({}))) as {
        success?: boolean;
        message?: string;
        details?: { fieldErrors?: Record<string, string[]> };
      };

      if (!response.ok || !body.success) {
        const first = body.details?.fieldErrors
          ? Object.values(body.details.fieldErrors)[0]?.[0]
          : undefined;
        setError(first ?? body.message ?? 'Could not submit the review.');
        setPending(false);
        return;
      }

      notify('Review submitted');
      setDone(true);
    } catch {
      setError('Network error. Please try again.');
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="rounded-panel border border-line bg-surface/50 p-5" noValidate>
      <h3 className="font-display text-base font-600 text-heading">Write a review</h3>
      <p className="mt-1 text-xs text-muted">Published after moderation. Your email is never shown.</p>

      <fieldset className="mt-4">
        <legend className="text-sm font-medium text-heading">Rating</legend>
        <div className="mt-2 flex gap-1">
          {[1, 2, 3, 4, 5].map((value) => (
            <button
              key={value}
              type="button"
              aria-label={`${value} star${value === 1 ? '' : 's'}`}
              aria-pressed={rating === value}
              onClick={() => setRating(value)}
              className={
                value <= rating
                  ? 'text-2xl leading-none text-amber-300'
                  : 'text-2xl leading-none text-line transition-colors hover:text-amber-200'
              }
            >
              ★
            </button>
          ))}
        </div>
      </fieldset>

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <Field id="authorName" label="Name">
          <Input id="authorName" name="authorName" required minLength={2} autoComplete="name" />
        </Field>
        <Field id="authorEmail" label="Email" hint="Not published">
          <Input id="authorEmail" name="authorEmail" type="email" required autoComplete="email" />
        </Field>
      </div>

      <div className="mt-4">
        <Field id="title" label="Headline" hint="Optional">
          <Input id="title" name="title" maxLength={120} />
        </Field>
      </div>

      <div className="mt-4">
        <Field id="comment" label="Review" hint="10–2000 characters">
          <Textarea id="comment" name="comment" required minLength={10} maxLength={2000} rows={3} />
        </Field>
      </div>

      {error && (
        <p role="alert" className="mt-3 text-sm font-medium text-red-400">
          {error}
        </p>
      )}

      <Button type="submit" className="mt-4" disabled={pending}>
        {pending ? (
          <>
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
            Submitting…
          </>
        ) : (
          'Submit review'
        )}
      </Button>
    </form>
  );
}
