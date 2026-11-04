'use client';

import { useState } from 'react';
import { Loader2, Mail } from 'lucide-react';

export function NewsletterForm() {
  const [state, setState] = useState<'idle' | 'sending' | 'done' | 'error'>('idle');
  const [message, setMessage] = useState('');

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (state === 'sending') return;
    setState('sending');
    setMessage('');

    const form = new FormData(event.currentTarget);
    try {
      const response = await fetch('/api/newsletter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: String(form.get('email') ?? ''), source: 'footer' }),
      });
      const body = (await response.json()) as {
        success: boolean;
        message?: string;
        details?: { fieldErrors?: Record<string, string[]> };
      };

      if (!response.ok || !body.success) {
        const first = body.details?.fieldErrors
          ? Object.values(body.details.fieldErrors)[0]?.[0]
          : undefined;
        setMessage(first ?? body.message ?? 'Could not subscribe. Try again.');
        setState('error');
        return;
      }

      setMessage('You are on the list. We email when something worth seeing lands.');
      setState('done');
    } catch {
      setMessage('Network error. Please try again.');
      setState('error');
    }
  }

  if (state === 'done') {
    return (
      <p role="status" className="text-sm leading-relaxed text-emerald-300">
        {message}
      </p>
    );
  }

  return (
    <form onSubmit={onSubmit} className="space-y-2" noValidate>
      <label htmlFor="newsletter-email" className="block text-xs font-semibold uppercase tracking-[0.18em] text-heading">
        New arrivals
      </label>
      <p className="text-xs leading-relaxed text-muted">
        One email when a car worth seeing lands. No newsletter churn.
      </p>
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Mail className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted" aria-hidden="true" />
          <input
            id="newsletter-email"
            name="email"
            type="email"
            required
            placeholder="you@example.com"
            autoComplete="email"
            className="w-full rounded-control border border-line bg-canvas/70 py-2 pl-8 pr-3 text-sm text-heading placeholder:text-muted/70 focus:border-primary focus:outline-none"
          />
        </div>
        <button
          type="submit"
          disabled={state === 'sending'}
          className="inline-flex items-center gap-1.5 rounded-control bg-primary px-3 py-2 text-sm font-semibold text-[#0b0616] transition-colors hover:bg-accent disabled:opacity-60"
        >
          {state === 'sending' ? <Loader2 className="size-3.5 animate-spin" aria-hidden="true" /> : 'Join'}
        </button>
      </div>
      {message && state === 'error' && (
        <p role="alert" className="text-xs font-medium text-red-400">
          {message}
        </p>
      )}
    </form>
  );
}
