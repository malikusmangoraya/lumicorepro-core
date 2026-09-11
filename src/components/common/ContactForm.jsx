/**
 * ContactForm — reusable contact / lead form with explicit state handlers.
 * Validates client-side, submits via contactAPI (Formspree / webhook / mock),
 * and reports status through both inline alerts and onSuccess/onError callbacks.
 */
import { useMemo, useState } from 'react';
import { Button, Input, Textarea, Alert } from '@/components/ui';
import useForm from '@/hooks/useForm';
import { contactAPI } from '@/services/contact';

const INITIAL_VALUES = { name: '', email: '', subject: '', message: '', consent: false };

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const validate = (values) => {
  const errors = {};
  if (!values.name.trim()) errors.name = 'Name is required';
  if (!values.email.trim()) {
    errors.email = 'Email is required';
  } else if (!EMAIL_RE.test(values.email.trim())) {
    errors.email = 'Enter a valid email address';
  }
  if (!values.message.trim()) {
    errors.message = 'Message is required';
  } else if (values.message.trim().length < 10) {
    errors.message = 'Message must be at least 10 characters';
  }
  if (!values.consent) errors.consent = 'Please accept the privacy policy';
  return errors;
};

export default function ContactForm({
  onSuccess,
  onError,
  submitLabel = 'Send message',
  className = '',
}) {
  const [status, setStatus] = useState(null);

  const submitContact = useMemo(
    () => async (values) => {
      setStatus(null);
      try {
        const result = await contactAPI.postLead({
          name: values.name.trim(),
          email: values.email.trim(),
          subject: values.subject.trim() || 'Website contact',
          message: values.message.trim(),
          consent: values.consent,
        });
        setStatus({
          type: 'success',
          message: result.mock
            ? 'Message queued — connect Formspree or a webhook to deliver it.'
            : 'Message sent — we reply within one business day.',
        });
        if (onSuccess) onSuccess(result);
      } catch (err) {
        setStatus({
          type: 'error',
          message: 'Sorry, we could not send your message. Please try again.',
        });
        if (onError) onError(err);
        throw err;
      }
    },
    [onSuccess, onError]
  );

  const form = useForm({
    initialValues: INITIAL_VALUES,
    validate,
    onSubmit: submitContact,
  });

  return (
    <div className={`space-y-4 ${className}`}>
      {status && (
        <Alert
          variant={status.type}
          title={status.type === 'success' ? 'Message sent' : 'Something went wrong'}
          dismissible
          onDismiss={() => setStatus(null)}
        >
          {status.message}
        </Alert>
      )}

      <form onSubmit={form.handleSubmit} noValidate className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input
            label="Name"
            name="name"
            required
            autoComplete="name"
            value={form.values.name}
            onChange={form.handleChange}
            onBlur={form.handleBlur}
            error={form.touched.name && form.errors.name}
          />
          <Input
            label="Email"
            name="email"
            type="email"
            required
            autoComplete="email"
            value={form.values.email}
            onChange={form.handleChange}
            onBlur={form.handleBlur}
            error={form.touched.email && form.errors.email}
          />
        </div>

        <Input
          label="Subject"
          name="subject"
          value={form.values.subject}
          onChange={form.handleChange}
          onBlur={form.handleBlur}
          error={form.touched.subject && form.errors.subject}
        />

        <Textarea
          label="Message"
          name="message"
          rows={5}
          required
          value={form.values.message}
          onChange={form.handleChange}
          onBlur={form.handleBlur}
          error={form.touched.message && form.errors.message}
        />

        <label className="flex items-start gap-2 text-sm text-muted-foreground cursor-pointer">
          <input
            type="checkbox"
            name="consent"
            checked={form.values.consent}
            onChange={form.handleChange}
            className="mt-0.5 h-4 w-4 rounded border-border accent-primary"
            aria-invalid={!!(form.touched.consent && form.errors.consent)}
          />
          <span>
            I agree to the privacy policy and consent to being contacted about my inquiry.
          </span>
        </label>
        {form.touched.consent && form.errors.consent && (
          <p className="text-xs text-destructive" role="alert">
            {form.errors.consent}
          </p>
        )}

        <Button type="submit" loading={form.isSubmitting} className="w-full sm:w-auto">
          {submitLabel}
        </Button>
      </form>
    </div>
  );
}
