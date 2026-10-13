import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import vehicleApi from '../../services/vehicleApi';

const newKey = () => globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}`;

export default function VehicleInquiryForm({ vehicleId }) {
  const [message, setMessage] = useState('');
  const [feedback, setFeedback] = useState(null);
  const [idempotencyKey, setIdempotencyKey] = useState(newKey);
  const mutation = useMutation({ mutationFn: (payload) => vehicleApi.submitInquiry(payload) });

  async function submit(event) {
    event.preventDefault();
    const form = event.currentTarget;
    if (!form.reportValidity()) return;
    const fields = new FormData(form);
    const payload = {
      name: String(fields.get('name') || ''),
      email: String(fields.get('email') || ''),
      phone: String(fields.get('phone') || ''),
      message,
      ...(vehicleId ? { vehicleId } : {}),
      consent_given: fields.get('consent') === 'on',
      locale: document.documentElement.lang || 'en',
      idempotency_key: idempotencyKey,
    };
    try {
      await mutation.mutateAsync(payload);
      setFeedback({ success: true, text: 'Your enquiry has been received. An advisor will follow up.' });
      form.reset();
      setMessage('');
      setIdempotencyKey(newKey());
    } catch (error) {
      setFeedback({ success: false, text: error.response?.data?.message || 'We couldn’t send your enquiry. Please try again.' });
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4 border border-[var(--t-border)] bg-surface p-6" aria-label={vehicleId ? 'Vehicle enquiry' : 'Contact enquiry'}>
      <h2 className="text-xl font-bold">{vehicleId ? 'Ask about this vehicle' : 'Send an enquiry'}</h2>
      <label className="block text-sm font-medium">Your name<input name="name" required minLength={2} maxLength={120} autoComplete="name" className="mt-1 block w-full rounded border border-[var(--t-border)] bg-canvas px-3 py-2" /></label>
      <label className="block text-sm font-medium">Email address<input name="email" type="email" required maxLength={160} autoComplete="email" className="mt-1 block w-full rounded border border-[var(--t-border)] bg-canvas px-3 py-2" /></label>
      <label className="block text-sm font-medium">Phone (optional)<input name="phone" type="tel" maxLength={40} autoComplete="tel" className="mt-1 block w-full rounded border border-[var(--t-border)] bg-canvas px-3 py-2" /></label>
      <label className="block text-sm font-medium">Message<textarea name="message" required minLength={10} maxLength={5000} value={message} onChange={(event) => setMessage(event.target.value)} className="mt-1 block w-full rounded border border-[var(--t-border)] bg-canvas px-3 py-2" rows={4} /></label>
      <label className="flex items-start gap-3 text-sm"><input name="consent" type="checkbox" required className="mt-1" /><span>I agree that Apex may use these details to respond to my enquiry. See the <a className="underline" href="/privacy">Privacy notice</a>.</span></label>
      {feedback && <p role={feedback.success ? 'status' : 'alert'} className={feedback.success ? 'text-emerald-700' : 'text-red-700'}>{feedback.text}</p>}
      <button type="submit" disabled={mutation.isPending} className="btn-primary disabled:cursor-not-allowed disabled:opacity-60">{mutation.isPending ? 'Sending…' : 'Send enquiry'}</button>
    </form>
  );
}
