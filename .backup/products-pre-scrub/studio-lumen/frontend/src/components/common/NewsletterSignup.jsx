import React, { useState } from 'react';
import { Mail, Send, CheckCircle2 } from 'lucide-react';
import { cn } from '../../utils';
import Spinner from '../ui/Spinner';

const NewsletterSignup = ({
  title = 'Stay in the loop',
  subtitle = 'Subscribe for product updates, tips and exclusive offers. No spam, ever.',
  buttonLabel = 'Subscribe',
  placeholder = 'Enter your email',
  onSubscribe,
  className = '',
}) => {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState('idle');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus('loading');
    try {
      if (typeof onSubscribe === 'function') {
        await onSubscribe(email);
      }
      setStatus('success');
      setEmail('');
    } catch (err) {
      setStatus('error');
    }
  };

  return (
    <section
      className={cn(
        'w-full rounded-2xl border bg-card p-8 text-card-foreground sm:p-10',
        className
      )}
    >
      <div className="mx-auto max-w-2xl space-y-4 text-center">
        <span className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
          <Mail className="h-5 w-5 text-primary" aria-hidden="true" />
        </span>
        <h2 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">{title}</h2>
        <p className="text-sm text-muted-foreground sm:text-base">{subtitle}</p>

        {status === 'success' ? (
          <div
            role="status"
            className="flex items-center justify-center gap-2 rounded-lg border border-green-600/30 bg-green-600/10 px-4 py-3 text-sm font-medium text-green-700 dark:text-green-400"
          >
            <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
            Thanks! Please check your inbox to confirm.
          </div>
        ) : (
          <form
            onSubmit={handleSubmit}
            className="mx-auto flex max-w-md flex-col gap-3 sm:flex-row"
          >
            <label htmlFor="newsletter-email" className="sr-only">
              Email address
            </label>
            <input
              id="newsletter-email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={placeholder}
              className="flex-1 rounded-lg border bg-background px-4 py-2.5 text-sm text-foreground outline-none transition-all duration-200 focus:border-primary focus:ring-2 focus:ring-primary/30"
            />
            <button
              type="submit"
              disabled={status === 'loading'}
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition-all duration-200 hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/40 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {status === 'loading' ? (
                <Spinner size="sm" color="white" />
              ) : (
                <Send className="h-4 w-4" aria-hidden="true" />
              )}
              {buttonLabel}
            </button>
          </form>
        )}

        <p className="text-xs text-muted-foreground">
          By subscribing you agree to our privacy policy and consent to occasional emails.
        </p>
      </div>
    </section>
  );
};

export default NewsletterSignup;
