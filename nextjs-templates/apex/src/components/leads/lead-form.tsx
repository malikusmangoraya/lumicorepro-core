'use client';

import { useState } from 'react';
import { CheckCircle2, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Field, Input, Select, Textarea } from '@/components/ui/field';
import { useSite } from '@/components/providers/site-provider';
import type { LeadType } from '@/lib/validation';

const COPY: Record<LeadType, { submit: string; messageLabel: string; messagePlaceholder: string }> = {
  general: {
    submit: 'Send enquiry',
    messageLabel: 'Message',
    messagePlaceholder: "I'd like to know more about this car.",
  },
  test_drive: {
    submit: 'Request test drive',
    messageLabel: 'Anything we should know?',
    messagePlaceholder: 'I can only do mornings, and I would like to bring a friend.',
  },
  finance: {
    submit: 'Request a finance quote',
    messageLabel: 'Anything else?',
    messagePlaceholder: 'I have a part exchange and would like to settle the rest over 48 months.',
  },
  trade_in: {
    submit: 'Get a valuation',
    messageLabel: 'Condition and history',
    messagePlaceholder: 'Two owners, full service history, small scuff on the rear bumper.',
  },
};

export function LeadForm({
  type,
  vehicleSlug,
  vehicleTitle,
  compact = false,
}: {
  type: LeadType;
  vehicleSlug?: string;
  vehicleTitle?: string;
  compact?: boolean;
}) {
  const { notify } = useSite();
  const [pending, setPending] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Generated once per mount so a double submit is de-duplicated by the server.
  const [idempotencyKey] = useState(() => crypto.randomUUID());

  const copy = COPY[type];

  if (done) {
    return (
      <div role="status" className="rounded-panel border border-emerald-500/30 bg-emerald-500/5 p-5">
        <div className="flex items-start gap-3">
          <CheckCircle2 className="mt-0.5 size-5 text-emerald-400" aria-hidden="true" />
          <div>
            <h3 className="font-600 text-heading">
              {type === 'test_drive'
                ? 'Test drive requested'
                : type === 'finance'
                  ? 'Finance request received'
                  : type === 'trade_in'
                    ? 'Valuation requested'
                    : 'Enquiry received'}
            </h3>
            <p className="mt-1 text-sm leading-relaxed text-muted">
              A specialist replies within one business day. Nothing is booked or charged yet.
            </p>
          </div>
        </div>
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

    const metadata: Record<string, string> = {};
    if (type === 'test_drive') {
      metadata.date = text('date');
      metadata.time = text('time');
    }
    if (type === 'finance') {
      metadata.deposit = text('deposit');
      metadata.term = text('term');
    }
    if (type === 'trade_in') {
      metadata.registration = text('registration');
      metadata.makeModel = text('makeModel');
      metadata.mileage = text('mileage');
    }

    try {
      const response = await fetch('/api/leads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type,
          name: text('name'),
          email: text('email'),
          phone: text('phone'),
          message: text('message') || copy.messagePlaceholder,
          vehicleSlug: vehicleSlug ?? '',
          metadata,
          consentGiven: form.get('consent') === 'on',
          idempotencyKey,
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
        setError(first ?? body.message ?? 'Could not send your request.');
        setPending(false);
        return;
      }

      notify('Request sent');
      setDone(true);
    } catch {
      setError('Network error. Please try again.');
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4" noValidate>
      {vehicleTitle && (
        <p className="rounded-control border border-line bg-canvas/50 px-3 py-2 text-xs text-muted">
          About: <span className="text-heading">{vehicleTitle}</span>
        </p>
      )}

      <div className={compact ? 'space-y-4' : 'grid gap-4 sm:grid-cols-2'}>
        <Field id={`lead-name-${type}`} label="Name">
          <Input id={`lead-name-${type}`} name="name" required minLength={2} autoComplete="name" />
        </Field>
        <Field id={`lead-email-${type}`} label="Email">
          <Input id={`lead-email-${type}`} name="email" type="email" required autoComplete="email" />
        </Field>
        <Field id={`lead-phone-${type}`} label="Phone" hint="Optional">
          <Input id={`lead-phone-${type}`} name="phone" type="tel" autoComplete="tel" />
        </Field>

        {type === 'test_drive' && (
          <>
            <Field id={`lead-date-${type}`} label="Preferred date">
              <Input id={`lead-date-${type}`} name="date" type="date" required />
            </Field>
            <Field id={`lead-time-${type}`} label="Preferred time">
              <Select id={`lead-time-${type}`} name="time" defaultValue="10:00">
                {['09:00', '10:00', '11:00', '13:00', '14:00', '15:00', '16:00'].map((slot) => (
                  <option key={slot} value={slot}>
                    {slot}
                  </option>
                ))}
              </Select>
            </Field>
          </>
        )}

        {type === 'finance' && (
          <>
            <Field id={`lead-deposit-${type}`} label="Deposit" hint="Amount you can put down">
              <Input
                id={`lead-deposit-${type}`}
                name="deposit"
                type="number"
                min={0}
                step={500}
                required
                placeholder="10000"
              />
            </Field>
            <Field id={`lead-term-${type}`} label="Preferred term">
              <Select id={`lead-term-${type}`} name="term" defaultValue="48">
                {[24, 36, 48, 60, 72].map((term) => (
                  <option key={term} value={term}>
                    {term} months
                  </option>
                ))}
              </Select>
            </Field>
          </>
        )}

        {type === 'trade_in' && (
          <>
            <Field id={`lead-registration-${type}`} label="Registration">
              <Input
                id={`lead-registration-${type}`}
                name="registration"
                required
                maxLength={16}
                placeholder="CA 1234"
              />
            </Field>
            <Field id={`lead-makeModel-${type}`} label="Make and model">
              <Input id={`lead-makeModel-${type}`} name="makeModel" placeholder="Audi S3" />
            </Field>
            <Field id={`lead-mileage-${type}`} label="Mileage">
              <Input id={`lead-mileage-${type}`} name="mileage" type="number" min={0} step={1000} />
            </Field>
          </>
        )}

        <div className={compact ? '' : 'sm:col-span-2'}>
          <Field id={`lead-message-${type}`} label={copy.messageLabel} hint="5–2000 characters">
            <Textarea
              id={`lead-message-${type}`}
              name="message"
              required
              minLength={5}
              maxLength={2000}
              rows={3}
              placeholder={copy.messagePlaceholder}
            />
          </Field>
        </div>
      </div>

      <label className="flex items-start gap-3 text-sm text-muted">
        <input
          type="checkbox"
          name="consent"
          required
          className="mt-0.5 size-4 rounded border-line bg-canvas accent-primary"
        />
        <span>
          I agree to be contacted about this request and have read the{' '}
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

      <Button type="submit" disabled={pending} fullWidth>
        {pending ? (
          <>
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
            Sending…
          </>
        ) : (
          copy.submit
        )}
      </Button>
    </form>
  );
}
