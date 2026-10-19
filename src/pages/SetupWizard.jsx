import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Rocket, Check, ArrowRight, ArrowLeft, Shield, Building2, CreditCard } from 'lucide-react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle, Button, Alert } from '../components/ui';
import { Input, Switch, Select } from '../components/forms';
import settingsApi from '../services/settingsApi';
import { useAppContext } from '../context/AppContext';
import { trackEvent, AnalyticsEvents } from '../utils/analytics';

const CURRENCIES = [
  { code: 'USD', label: 'US Dollar ($)' },
  { code: 'EUR', label: 'Euro (€)' },
  { code: 'GBP', label: 'British Pound (£)' },
  { code: 'PKR', label: 'Pakistani Rupee (Rs)' },
  { code: 'INR', label: 'Indian Rupee (₹)' },
  { code: 'AED', label: 'UAE Dirham (د.إ)' },
  { code: 'SAR', label: 'Saudi Riyal (﷼)' },
  { code: 'JPY', label: 'Japanese Yen (¥)' },
  { code: 'CNY', label: 'Chinese Yuan (¥)' },
  { code: 'BRL', label: 'Brazilian Real (R$)' },
  { code: 'MXN', label: 'Mexican Peso ($)' },
  { code: 'CAD', label: 'Canadian Dollar ($)' },
  { code: 'AUD', label: 'Australian Dollar ($)' },
  { code: 'SGD', label: 'Singapore Dollar ($)' },
  { code: 'BDT', label: 'Bangladeshi Taka (৳)' },
  { code: 'TRY', label: 'Turkish Lira (₺)' },
];

const STEPS = [
  { id: 0, label: 'Admin Account', icon: Shield },
  { id: 1, label: 'Business Details', icon: Building2 },
  { id: 2, label: 'Payments (Optional)', icon: CreditCard },
];

export default function SetupWizard() {
  const navigate = useNavigate();
  const app = useAppContext();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [admin, setAdmin] = useState({ name: '', email: '', password: '', confirmPassword: '' });
  const [business, setBusiness] = useState({ name: '', tagline: '', logoUrl: '', supportEmail: '', niche: '' });
  const [currency, setCurrency] = useState('USD');
  const [stripe, setStripe] = useState({
    enabled: false,
    mode: 'sandbox',
    secretKey: '',
    publishableKey: '',
    webhookSecret: '',
  });

  const setField = (group, key) => (e) => {
    const { value } = e.target;
    if (group === 'admin') setAdmin((p) => ({ ...p, [key]: value }));
    if (group === 'business') setBusiness((p) => ({ ...p, [key]: value }));
    if (group === 'stripe') setStripe((p) => ({ ...p, [key]: value }));
  };

  const validateStep = () => {
    setError('');
    if (step === 0) {
      if (!admin.name.trim()) return 'Admin name is required';
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(admin.email)) return 'Valid admin email is required';
      if (admin.password.length < 8) return 'Password must be at least 8 characters';
      if (admin.password !== admin.confirmPassword) return 'Passwords do not match';
    }
    if (step === 1) {
      if (!business.name.trim()) return 'Business name is required';
    }
    return '';
  };

  const next = () => {
    const v = validateStep();
    if (v) {
      setError(v);
      return;
    }
    if (step === STEPS.length - 1) return submit();
    setStep((s) => s + 1);
  };

  const submit = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await settingsApi.setup({
        admin: { name: admin.name, email: admin.email, password: admin.password },
        business: {
          name: business.name,
          tagline: business.tagline,
          logoUrl: business.logoUrl,
          supportEmail: business.supportEmail || admin.email,
          niche: business.niche,
        },
        currency: { code: currency },
        payments: { stripe },
      });
      trackEvent('setup_complete');
      if (data?.token && data?.user) {
        app.login(data.user, data.token);
      }
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Setup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl py-10">
      <div className="mb-10 text-center">
        <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
          <Rocket className="h-7 w-7" aria-hidden="true" />
        </div>
        <h1 className="font-display mt-4 text-3xl font-bold text-foreground">
          Welcome to LumicorePro
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Get your business online in under 5 minutes — no code, no terminal.
        </p>
      </div>

      <ol className="mb-8 flex items-center justify-center gap-2" aria-label="Setup progress">
        {STEPS.map((s) => {
          const Icon = s.icon;
          const isActive = step === s.id;
          const isDone = step > s.id;
          return (
            <li key={s.id} className="flex items-center gap-2" aria-current={isActive ? 'step' : undefined}>
              <span
                className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : isDone
                    ? 'bg-primary/15 text-primary'
                    : 'bg-muted text-muted-foreground'
                }`}
              >
                {isDone ? <Check className="h-3.5 w-3.5" aria-hidden="true" /> : <Icon className="h-3.5 w-3.5" aria-hidden="true" />}
                {s.label}
              </span>
              {s.id < STEPS.length - 1 && <span className="h-px w-6 bg-border" aria-hidden="true" />}
            </li>
          );
        })}
      </ol>

      <Card>
        <CardHeader>
          <CardTitle>{STEPS[step].label}</CardTitle>
          <CardDescription>
            {step === 0 && 'Create the master Super-Admin account for your site.'}
            {step === 1 && 'Tell us about your business — this powers branding, emails and currency.'}
            {step === 2 && 'Optional: connect Stripe now or add keys later from the Admin Settings panel.'}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && <Alert variant="danger">{error}</Alert>}

          {step === 0 && (
            <>
              <Input
                label="Full Name"
                value={admin.name}
                onChange={setField('admin', 'name')}
                placeholder="Jane Doe"
                autoComplete="name"
                required
              />
              <Input
                label="Admin Email"
                type="email"
                value={admin.email}
                onChange={setField('admin', 'email')}
                placeholder="you@company.com"
                autoComplete="email"
                required
              />
              <Input
                label="Password"
                type="password"
                value={admin.password}
                onChange={setField('admin', 'password')}
                placeholder="Minimum 8 characters"
                autoComplete="new-password"
                required
              />
              <Input
                label="Confirm Password"
                type="password"
                value={admin.confirmPassword}
                onChange={setField('admin', 'confirmPassword')}
                placeholder="Repeat password"
                autoComplete="new-password"
                required
              />
            </>
          )}

          {step === 1 && (
            <>
              <Input
                label="Business Name"
                value={business.name}
                onChange={setField('business', 'name')}
                placeholder="Acme Wellness"
                required
              />
              <Input
                label="Tagline (optional)"
                value={business.tagline}
                onChange={setField('business', 'tagline')}
                placeholder="Health & wellness for everyone"
              />
              <Input
                label="Logo URL (optional)"
                value={business.logoUrl}
                onChange={setField('business', 'logoUrl')}
                placeholder="https://yourcdn.com/logo.png"
              />
              <Input
                label="Support Email"
                type="email"
                value={business.supportEmail}
                onChange={setField('business', 'supportEmail')}
                placeholder="support@company.com"
                helperText="Defaults to your admin email when left empty"
              />
              <Select label="Base Currency" value={currency} onChange={(e) => setCurrency(e.target.value)} required>
                {CURRENCIES.map((c) => (
                  <option key={c.code} value={c.code}>
                    {c.label}
                  </option>
                ))}
              </Select>
              <Input
                label="Business Niche (optional)"
                value={business.niche}
                onChange={setField('business', 'niche')}
                placeholder="e.g. healthcare, ecommerce, fitness"
                helperText="Used to tailor sample data in your demo"
              />
            </>
          )}

          {step === 2 && (
            <>
              <div className="flex items-center justify-between rounded-lg border border-border p-4">
                <div>
                  <p className="text-sm font-medium text-foreground">Enable Stripe (test mode)</p>
                  <p className="text-xs text-muted-foreground">Toggle Sandbox/Live later in Admin Settings</p>
                </div>
                <Switch checked={stripe.enabled} onChange={(checked) => setStripe((p) => ({ ...p, enabled: checked }))} aria-label="Enable Stripe" />
              </div>
              {stripe.enabled && (
                <>
                  <Select
                    label="Environment"
                    value={stripe.mode}
                    onChange={(e) => setStripe((p) => ({ ...p, mode: e.target.value }))}
                  >
                    <option value="sandbox">Sandbox (Test)</option>
                    <option value="live">Live (Production)</option>
                  </Select>
                  <Input
                    label="Stripe Secret Key"
                    type="password"
                    value={stripe.secretKey}
                    onChange={setField('stripe', 'secretKey')}
                    placeholder="sk_test_..."
                  />
                  <Input
                    label="Stripe Publishable Key"
                    value={stripe.publishableKey}
                    onChange={setField('stripe', 'publishableKey')}
                    placeholder="pk_test_..."
                  />
                  <Input
                    label="Webhook Secret (optional)"
                    type="password"
                    value={stripe.webhookSecret}
                    onChange={setField('stripe', 'webhookSecret')}
                    placeholder="whsec_..."
                  />
                </>
              )}
              <p className="text-xs text-muted-foreground">
                You can always connect payment + email credentials later from the Admin Dashboard →
                Global System Settings panel.
              </p>
            </>
          )}
        </CardContent>
        <CardFooter className="justify-between">
          <Button
            variant="ghost"
            onClick={() => (step === 0 ? navigate('/login') : setStep((s) => s - 1))}
            disabled={loading}
          >
            <ArrowLeft className="mr-2 h-4 w-4" aria-hidden="true" />
            {step === 0 ? 'Back' : 'Previous'}
          </Button>
          <Button onClick={next} disabled={loading} leftIcon={step === STEPS.length - 1 ? Check : ArrowRight}>
            {loading ? 'Setting up…' : step === STEPS.length - 1 ? 'Finish Setup' : 'Continue'}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}