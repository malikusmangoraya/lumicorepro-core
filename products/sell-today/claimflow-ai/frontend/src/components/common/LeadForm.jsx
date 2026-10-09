/**
 * LeadForm — conversion lead capture on the resolved provider pipeline.
 * Auto-generated utility — project primitive.
 * Endpoint resolution: Formspree -> generic webhook -> dev mock (no network).
 * Honeypot + status feedback + analytics events included.
 */
import { useState } from 'react';
import ButtonMotion from '@/components/ui/ButtonMotion';
import { track } from '../../services/analyticsBus';

const RESOLVE_ENDPOINT = (formId) => {
  const formspree = import.meta.env.VITE_FORMSPREE_ID;
  const webhook = import.meta.env.VITE_LEADS_WEBHOOK;
  if (formspree) return `https://formspree.io/f/${formspree}`;
  if (webhook) return webhook;
  return '/api/leads/mock';
};

export default function LeadForm({
  title = 'Get early access',
  cta = 'Send my info',
  formId = 'lead_form',
}) {
  const [status, setStatus] = useState('idle'); // idle | sending | success | error
  const [error, setError] = useState('');

  const onSubmit = async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.currentTarget));
    if (data.website) return; // honeypot
    setStatus('sending');
    track('lead_capture_start', { form_id: formId });
    try {
      const res = await fetch(RESOLVE_ENDPOINT(formId), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({
          name: data.name,
          email: data.email,
          message: data.message,
          _subject: `New lead: ${title}`,
        }),
      });
      if (!res.ok && res.status !== 400 && res.status !== 422)
        throw new Error(`HTTP ${res.status}`);
      setStatus('success');
      track('lead_captured', {
        form_id: formId,
        method: window.navigator.userAgent ? 'webform' : 'webform',
      });
    } catch (err) {
      setStatus('error');
      setError('Could not submit — please try again or email us directly.');
    }
  };

  return (
    <form onSubmit={onSubmit} aria-label={title} className="glass-card space-y-3 p-6">
      <h3 className="text-lg font-semibold">{title}</h3>
      <div className="hidden" aria-hidden="true">
        <label>
          Website
          <input type="text" name="website" tabIndex={-1} autoComplete="off" />
        </label>
      </div>
      <div>
        <label className="mb-1 block text-sm" htmlFor={`${formId}-name`}>
          Name
        </label>
        <input
          id={`${formId}-name`}
          name="name"
          required
          className="w-full rounded-lg border border-slate-700 bg-slate-900 p-2"
        />
      </div>
      <div>
        <label className="mb-1 block text-sm" htmlFor={`${formId}-email`}>
          Email
        </label>
        <input
          id={`${formId}-email`}
          name="email"
          type="email"
          required
          autoComplete="email"
          className="w-full rounded-lg border border-slate-700 bg-slate-900 p-2"
        />
      </div>
      <div>
        <label className="mb-1 block text-sm" htmlFor={`${formId}-msg`}>
          Message
        </label>
        <textarea
          id={`${formId}-msg`}
          name="message"
          rows={3}
          className="w-full rounded-lg border border-slate-700 bg-slate-900 p-2"
        />
      </div>
      {status === 'error' && (
        <p role="alert" className="text-sm text-rose-400">
          {error}
        </p>
      )}
      {status === 'success' && (
        <p role="status" className="text-sm text-emerald-400">
          Thanks! We will be in touch shortly.
        </p>
      )}
      <ButtonMotion
        type="submit"
        disabled={status === 'sending'}
        className="w-full rounded-lg bg-cyan-600 px-4 py-2 font-semibold text-white transition hover:bg-cyan-500 disabled:opacity-60"
      >
        {status === 'sending' ? 'Sending…' : cta}
      </ButtonMotion>
    </form>
  );
}
