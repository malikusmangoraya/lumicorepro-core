import { useMemo, useState } from 'react';
import { Mail, Phone, MapPin, Send, ChevronDown, ChevronUp, CircleCheck } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button, Input, Textarea, Alert } from '@/components/ui';
import { img } from '@/utils/images';
import { contactInfo, faqs } from './data/mockData';
import { contactAPI } from '@/services/contact';

const ICONS = [Mail, Phone, MapPin];
const BUDGET_OPTIONS = ['< Rs 100k', 'Rs 100k–500k', 'Rs 500k–2M', 'Rs 2M+'];

const INITIAL_STATE = { name: '', email: '', company: '', budget: '', message: '' };

const validate = (values) => {
  const errors = {};
  if (!values.name.trim()) errors.name = 'Name is required';
  if (!values.email.trim()) {
    errors.email = 'Email is required';
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email.trim())) {
    errors.email = 'Enter a valid email address';
  }
  if (!values.message.trim()) {
    errors.message = 'Message is required';
  } else if (values.message.trim().length < 10) {
    errors.message = 'Message must be at least 10 characters';
  }
  return errors;
};

export default function ContactMe() {
  const [sent, setSent] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});
  const [apiError, setApiError] = useState('');
  const [values, setValues] = useState(INITIAL_STATE);
  const [openFaq, setOpenFaq] = useState(0);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setValues((prev) => ({ ...prev, [name]: value }));
    setFieldErrors((prev) => {
      const updated = { ...prev };
      delete updated[name];
      return updated;
    });
  };

  const handleSubmit = useMemo(
    () => async (e) => {
      e.preventDefault();
      const errors = validate(values);
      setFieldErrors(errors);
      if (Object.keys(errors).length) return;

      setSubmitting(true);
      setApiError('');
      try {
        await contactAPI.postLead({
          name: values.name.trim(),
          email: values.email.trim(),
          subject: `Project inquiry — ${values.company || 'General'}`,
          message: `Company: ${values.company || '—'}\nBudget: ${values.budget || '—'}\n\n${values.message.trim()}`,
        });
        setSent(true);
        setValues(INITIAL_STATE);
      } catch {
        setApiError('Sorry, we could not send your message. Please try again.');
      } finally {
        setSubmitting(false);
      }
    },
    [values]
  );

  return (
    <TemplateShell
      title="Let's Work Together"
      description="Tell me about your project — I reply within one working day."
      category="Portfolio"
      actions={
        <Badge variant="success">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
          Taking new projects
        </Badge>
      }
    >
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Form */}
        <Card animate="fade-up" className="lg:col-span-3">
          {sent ? (
            <div className="text-center py-14">
              <div className="h-14 w-14 rounded-full bg-emerald-500/15 flex items-center justify-center mx-auto mb-4">
                <CircleCheck className="h-7 w-7 text-emerald-400" />
              </div>
              <h3 className="font-display text-2xl font-bold mb-2">Message Sent!</h3>
              <p className="text-sm text-muted-foreground mb-5">
                I'll get back to you within 24 hours. Meanwhile, check out my work page.
              </p>
              <Button variant="outline" onClick={() => setSent(false)}>
                Send Another
              </Button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} noValidate className="space-y-4">
              <h3 className="font-display text-lg font-bold">Send a Message</h3>
              {apiError && (
                <Alert variant="danger" title="Unable to send">
                  {apiError}
                </Alert>
              )}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="Your name"
                  name="name"
                  required
                  autoComplete="name"
                  value={values.name}
                  onChange={handleChange}
                  error={fieldErrors.name}
                  placeholder="e.g. Ayesha Khan"
                />
                <Input
                  label="Email"
                  name="email"
                  type="email"
                  required
                  autoComplete="email"
                  value={values.email}
                  onChange={handleChange}
                  error={fieldErrors.email}
                  placeholder="you@company.com"
                />
              </div>
              <Input
                label="Company / Project"
                name="company"
                value={values.company}
                onChange={handleChange}
                placeholder="e.g. Redesign for TechNex"
              />
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1 block">
                  Budget (optional)
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {BUDGET_OPTIONS.map((b) => (
                    <button
                      key={b}
                      type="button"
                      onClick={() =>
                        setValues((prev) => ({ ...prev, budget: prev.budget === b ? '' : b }))
                      }
                      className={`rounded-xl border bg-card py-2 text-xs font-medium transition-all ${
                        values.budget === b
                          ? 'border-primary text-primary'
                          : 'border-border hover:border-primary/50 text-foreground'
                      }`}
                    >
                      {b}
                    </button>
                  ))}
                </div>
              </div>
              <Textarea
                label="Project details"
                name="message"
                rows={5}
                required
                value={values.message}
                onChange={handleChange}
                error={fieldErrors.message}
                placeholder="What are we building? Timeline? Must-haves?"
              />
              <Button type="submit" loading={submitting} size="lg">
                <Send className="h-4 w-4 mr-1" />
                Send Message
              </Button>
            </form>
          )}
        </Card>

        {/* Info + FAQ */}
        <div className="lg:col-span-2 space-y-6">
          <Card animate="fade-up" animationDelay={80}>
            <div className="relative h-32 overflow-hidden rounded-xl mb-4">
              <img
                src={img.portfolio.workspace}
                alt="Workspace"
                className="h-full w-full object-cover"
              />
            </div>
            <div className="space-y-3">
              {contactInfo.map((c, i) => {
                const Icon = ICONS[i];
                return (
                  <div key={c.label} className="flex items-center gap-3">
                    <div className="h-9 w-9 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                      <Icon className="h-4 w-4 text-primary" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs text-muted-foreground">{c.label}</p>
                      <p className="text-sm font-semibold truncate">{c.value}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>

          <Card animate="fade-up" animationDelay={140} padding="sm">
            <h4 className="font-display font-bold mb-3">Quick Answers</h4>
            <div className="space-y-2">
              {faqs.map((f, i) => (
                <div key={f.q} className="rounded-xl border border-border overflow-hidden">
                  <button
                    type="button"
                    onClick={() => setOpenFaq(openFaq === i ? null : i)}
                    className="w-full flex items-center justify-between gap-2 p-3 text-sm font-semibold text-left"
                  >
                    {f.q}
                    {openFaq === i ? (
                      <ChevronUp className="h-4 w-4 shrink-0 text-muted-foreground" />
                    ) : (
                      <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
                    )}
                  </button>
                  {openFaq === i && (
                    <p className="px-3 pb-3 text-xs text-muted-foreground leading-relaxed">{f.a}</p>
                  )}
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </TemplateShell>
  );
}
