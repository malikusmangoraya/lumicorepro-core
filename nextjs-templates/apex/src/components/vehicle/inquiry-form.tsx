'use client';

import { useState } from 'react';
import { CheckCircle2, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Field, Input, Textarea } from '@/components/ui/field';

type State = 'idle' | 'submitting' | 'success' | 'error';

export function InquiryForm({ vehicleId, vehicleTitle }: { vehicleId?: string; vehicleTitle?: string }) {
  const [state, setState] = useState<State>('idle');
  const [error, setError] = useState<string | null>(null);
  // Generated once per mount so a double submit (or a retry) is deduplicated
  // by the server instead of creating two inquiries.
  const [idempotencyKey] = useState(() => crypto.randomUUID());

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (state === 'submitting') return;
    setState('submitting');
    setError(null);

    const form = new FormData(event.currentTarget);
    const payload = {
      vehicleId: vehicleId ?? null,
      name: String(form.get('name') ?? '').trim(),
      email: String(form.get('email') ?? '').trim(),
      phone: String(form.get('phone') ?? '').trim(),
      message: String(form.get('message') ?? '').trim(),
      consentGiven: form.get('consent') === 'on',
      locale: 'en',
      idempotencyKey,
    };

    try {
      const response = await fetch('/api/inquiries', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Idempotency-Key': idempotencyKey },
        body: JSON.stringify(payload),
      });
      const body = (await response.json()) as {
        success: boolean;
        message?: string;
        details?: { fieldErrors?: Record<string, string[]> };
      };

      if (!response.ok || !body.success) {
        const fieldErrors = body.details?.fieldErrors;
        const first = fieldErrors ? Object.values(fieldErrors)[0]?.[0] : undefined;
        setError(first ?? body.message ?? 'Could not send your message. Please try again.');
        setState('error');
        return;
      }
      setState('success');
    } catch {
      setError('Network error. Check your connection and try again.');
      setState('error');
    }
  }

  if (state === 'success') {
    return (
      <div role="status" className="rounded-panel border border-emerald-500/30 bg-emerald-500/5 p-6">
        <div className="flex items-start gap-3">
          <CheckCircle2 className="mt-0.5 size-5 text-emerald-400" aria-hidden="true" />
          <div>
            <h3 className="font-600 text-heading">Enquiry received</h3>
            <p className="mt-1 text-sm leading-relaxed text-muted">
              A specialist will reply within one business day
              {vehicleTitle ? ` about the ${vehicleTitle}` : ''}. We never share your details.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4" noValidate>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field id="name" label="Name">
          <Input id="name" name="name" required minLength={2} maxLength={120} autoComplete="name" />
        </Field>
        <Field id="email" label="Email">
          <Input
            id="email"
            name="email"
            type="email"
            required
            maxLength={160}
            autoComplete="email"
          />
        </Field>
      </div>

      <Field id="phone" label="Phone" hint="Optional">
        <Input id="phone" name="phone" type="tel" maxLength={40} autoComplete="tel" />
      </Field>

      <Field id="message" label="Message" hint="10–4000 characters">
        <Textarea
          id="message"
          name="message"
          required
          minLength={10}
          maxLength={4000}
          defaultValue={
            vehicleTitle ? `I'd like to know more about the ${vehicleTitle}.` : undefined
          }
        />
      </Field>

      <label className="flex items-start gap-3 text-sm text-muted">
        <input
          type="checkbox"
          name="consent"
          required
          className="mt-0.5 size-4 rounded border-line bg-canvas accent-primary"
        />
        <span>
          I agree to be contacted about this enquiry and have read the{' '}
          <a href="/privacy" className="text-accent underline-offset-2 hover:underline">
            privacy policy
          </a>
          .
        </span>
      </label>

      {error && (
        <p role="alert" className="text-sm font-medium text-red-400">
          {error}
        </p>
      )}

      <Button type="submit" disabled={state === 'submitting'} fullWidth>
        {state === 'submitting' ? (
          <>
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
            Sending…
          </>
        ) : (
          'Send enquiry'
        )}
      </Button>
    </form>
  );
}
