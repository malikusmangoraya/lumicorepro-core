/**
 * FooterNewsletter — footer signup wired to the real contact API.
 *
 * There is no separate newsletter endpoint in this project: signups go through
 * `services/contact.js` (Formspree → webhook → provider-less mock). When no
 * provider is configured the API reports `{ mock: true }` and this form says so
 * instead of faking a subscription.
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Mail, CheckCircle2, AlertCircle, Info, Loader2 } from 'lucide-react';
import Button from '../ui/Button';
import { contactAPI } from '../../services/contact';
import { cn } from '../../utils';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const STATUS_MESSAGES = {
  loading: { tone: 'text-muted-foreground', Icon: Loader2 },
  success: { tone: 'text-emerald-600 dark:text-emerald-400', Icon: CheckCircle2 },
  unconfigured: { tone: 'text-muted-foreground', Icon: Info },
  error: { tone: 'text-destructive', Icon: AlertCircle },
  invalid: { tone: 'text-destructive', Icon: AlertCircle },
};

export default function FooterNewsletter({ className = '' }) {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState('idle');

  const messages = {
    success: t('footer.newsletterSuccess', 'Thanks — check your inbox to confirm.'),
    unconfigured: t(
      'footer.newsletterUnconfigured',
      'Newsletter delivery is not configured here, so nothing was sent.'
    ),
    error: t('footer.newsletterError', 'We could not submit your signup. Please try again.'),
    invalid: t('footer.newsletterInvalid', 'Enter a valid email address.'),
    loading: t('footer.newsletterLoading', 'Sending…'),
  };

  const submit = async (event) => {
    event.preventDefault();
    const address = email.trim();
    if (!EMAIL_RE.test(address)) {
      setStatus('invalid');
      return;
    }

    setStatus('loading');
    try {
      const result = await contactAPI.postLead({
        name: 'Newsletter subscriber',
        email: address,
        subject: 'Newsletter signup',
        message: `Newsletter signup from the site footer (${address}).`,
        consent: true,
      });
      // `mock` means no provider is configured — claiming success would be a lie.
      setStatus(result?.mock ? 'unconfigured' : 'success');
      if (!result?.mock) setEmail('');
    } catch {
      setStatus('error');
    }
  };

  const isLoading = status === 'loading';
  const feedback = status !== 'idle' ? STATUS_MESSAGES[status] : null;
  const FeedbackIcon = feedback?.Icon;

  return (
    <div className={cn('w-full md:w-auto', className)}>
      <form onSubmit={submit} className="flex w-full items-center gap-2" noValidate>
        <div className="relative flex-1 md:w-72">
          <Mail
            className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden="true"
          />
          <label htmlFor="footer-newsletter-email" className="sr-only">
            {t('footer.newsletterLabel', 'Email address')}
          </label>
          <input
            id="footer-newsletter-email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(event) => {
              setEmail(event.target.value);
              if (status !== 'idle') setStatus('idle');
            }}
            placeholder={t('footer.newsletterPlaceholder', 'Enter your work email')}
            aria-describedby="footer-newsletter-status"
            className="w-full rounded-xl border border-border/80 bg-background/90 py-2.5 pl-9 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
        <Button type="submit" variant="primary" loading={isLoading} className="shrink-0">
          {isLoading
            ? t('footer.newsletterJoining', 'Joining…')
            : t('footer.newsletterSubmit', 'Subscribe')}
        </Button>
      </form>

      <p
        id="footer-newsletter-status"
        className={cn('mt-2 flex items-center gap-1.5 text-xs', feedback?.tone || 'sr-only')}
        role={status === 'error' || status === 'invalid' ? 'alert' : 'status'}
      >
        {FeedbackIcon && (
          <FeedbackIcon
            className={cn('h-3.5 w-3.5', isLoading && 'animate-spin')}
            aria-hidden="true"
          />
        )}
        {messages[status] || ''}
      </p>
    </div>
  );
}
