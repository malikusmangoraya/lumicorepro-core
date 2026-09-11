import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Save,
  Building2,
  CreditCard,
  Mail,
  Coins,
  ShieldAlert,
  Loader2,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, Button, Alert } from '../components/ui';
import { Input, Switch, Select } from '../components/forms';
import { useAppContext } from '../context/AppContext';
import settingsApi from '../services/settingsApi';
import { CURRENCY_LIST } from '../config/currencies';

/**
 * Admin → Global System Settings
 * No-code runtime configuration panel. Every field maps to the SystemConfig
 * table on the backend (payments, SMTP, currency, business identity) — no
 * environment variables or code edits required.
 */
export default function GlobalSystemSettings() {
  const navigate = useNavigate();
  const { user } = useAppContext();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [savedKeys, setSavedKeys] = useState(false);

  const [form, setForm] = useState({
    business: { name: '', tagline: '', logoUrl: '', supportEmail: '' },
    currency: { code: 'USD' },
    payments: {
      stripe: { enabled: false, mode: 'sandbox', secretKey: '', publishableKey: '', webhookSecret: '' },
      paypal: { enabled: false, mode: 'sandbox', clientId: '', clientSecret: '', webhookId: '' },
    },
    smtp: { enabled: false, host: '', port: 587, secure: false, user: '', pass: '', fromName: '', fromEmail: '' },
  });

  const setField = useCallback((group, key, value) => {
    setForm((p) => ({
      ...p,
      [group]: { ...p[group], [key]: value },
    }));
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await settingsApi.getSystem();
      if (data) {
        setForm({
          business: {
            name: data.business?.name || '',
            tagline: data.business?.tagline || '',
            logoUrl: data.business?.logoUrl || '',
            supportEmail: data.business?.supportEmail || '',
          },
          currency: { code: data.currency?.code || 'USD' },
          payments: {
            stripe: {
              enabled: data.payments?.stripe?.enabled || false,
              mode: data.payments?.stripe?.mode || 'sandbox',
              secretKey: data.payments?.stripe?.secretKey
                ? data.payments?.stripe?.secretKey
                : '',
              publishableKey: data.payments?.stripe?.publishableKey || '',
              webhookSecret: data.payments?.stripe?.webhookSecret || '',
            },
            paypal: {
              enabled: data.payments?.paypal?.enabled || false,
              mode: data.payments?.paypal?.mode || 'sandbox',
              clientId: data.payments?.paypal?.clientId || '',
              clientSecret: data.payments?.paypal?.clientSecret || '',
              webhookId: data.payments?.paypal?.webhookId || '',
            },
          },
          smtp: {
            enabled: data.smtp?.enabled || false,
            host: data.smtp?.host || '',
            port: data.smtp?.port || 587,
            secure: data.smtp?.secure || false,
            user: data.smtp?.user || '',
            pass: data.smtp?.pass || '',
            fromName: data.smtp?.fromName || '',
            fromEmail: data.smtp?.fromEmail || '',
          },
        });
        setSavedKeys(Boolean(data.payments?.stripe?.secretKey));
      }
    } catch (err) {
      if (err.response?.status === 403 || err.response?.status === 401) {
        setError('You need admin access to view system settings.');
      } else {
        setError(err.response?.data?.error || 'Unable to load system settings.');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      await settingsApi.updateSystem(form);
      setSuccess('Settings saved. Payment and email services reloaded instantly.');
      setSavedKeys(Boolean(form.payments.stripe.secretKey));
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save settings.');
    } finally {
      setSaving(false);
    }
  };

  if (!loading && user?.role !== 'admin') {
    return (
      <div className="mx-auto max-w-md py-16">
        <Alert variant="danger" title="Access denied">
          Only admin accounts can manage system settings.
        </Alert>
        <Button className="mt-4" variant="outline" onClick={() => navigate('/dashboard')}>
          Back to dashboard
        </Button>
      </div>
    );
  }

  const currencies = Object.entries(CURRENCY_LIST || {}).map(([code, c]) => (
    <option key={code} value={code}>
      {c.symbol} {code} — {c.name}
    </option>
  ));

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-8">
        <h1 className="font-display text-2xl font-bold text-foreground">Global System Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Configure payments, email, currency and branding without touching code or environment files.
        </p>
      </div>

      {error && <Alert variant="danger" className="mb-4" dismissible onDismiss={() => setError('')}>{error}</Alert>}
      {success && <Alert variant="success" className="mb-4" dismissible onDismiss={() => setSuccess('')}>{success}</Alert>}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-6 w-6 animate-spin text-primary" aria-hidden="true" />
        </div>
      ) : (
        <form onSubmit={save} className="space-y-6">
          {/* Business identity */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Building2 className="h-5 w-5 text-primary" aria-hidden="true" />
                Business Identity
              </CardTitle>
              <CardDescription>Name, logo and support contact shown across the site and invoices.</CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Input
                label="Business Name"
                value={form.business.name}
                onChange={(e) => setField('business', 'name', e.target.value)}
                placeholder="Acme Corporation"
                required
              />
              <Input
                label="Logo URL"
                value={form.business.logoUrl}
                onChange={(e) => setField('business', 'logoUrl', e.target.value)}
                placeholder="https://cdn.example.com/logo.png"
              />
              <Input
                label="Tagline"
                value={form.business.tagline}
                onChange={(e) => setField('business', 'tagline', e.target.value)}
                placeholder="Your value proposition"
              />
              <Input
                label="Support Email"
                type="email"
                value={form.business.supportEmail}
                onChange={(e) => setField('business', 'supportEmail', e.target.value)}
                placeholder="support@example.com"
                required
              />
            </CardContent>
          </Card>

          {/* Payment gateways */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="h-5 w-5 text-primary" aria-hidden="true" />
                Payment Gateways
              </CardTitle>
              <CardDescription>
                {savedKeys
                  ? 'Gateway keys are configured. Editing hides stored keys — leave blank to keep existing.'
                  : 'Insert API keys below. Until configured, checkout returns a friendly "unconfigured" message.'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-8">
              <section aria-label="Stripe configuration">
                <Switch
                  label="Enable Stripe"
                  checked={form.payments.stripe.enabled}
                  onChange={(e) => setField('payments', 'stripe', { ...form.payments.stripe, enabled: e.target.checked })}
                />
                <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <Select
                    label="Environment"
                    value={form.payments.stripe.mode}
                    onChange={(e) => setField('payments', 'stripe', { ...form.payments.stripe, mode: e.target.value })}
                  >
                    <option value="sandbox">Sandbox (Test)</option>
                    <option value="live">Live (Production)</option>
                  </Select>
                  <div className="sm:col-span-2 lg:col-span-1" />
                  <Input
                    label="Secret Key"
                    type="password"
                    value={form.payments.stripe.secretKey}
                    onChange={(e) => setField('payments', 'stripe', { ...form.payments.stripe, secretKey: e.target.value })}
                    placeholder={savedKeys ? '•••••••• (kept)' : 'sk_test_...'}
                  />
                  <Input
                    label="Publishable Key"
                    value={form.payments.stripe.publishableKey}
                    onChange={(e) => setField('payments', 'stripe', { ...form.payments.stripe, publishableKey: e.target.value })}
                    placeholder="pk_test_..."
                  />
                  <Input
                    label="Webhook Secret"
                    type="password"
                    value={form.payments.stripe.webhookSecret}
                    onChange={(e) => setField('payments', 'stripe', { ...form.payments.stripe, webhookSecret: e.target.value })}
                    placeholder={savedKeys ? '•••••••• (kept)' : 'whsec_...'}
                  />
                </div>
              </section>

              <section aria-label="PayPal configuration">
                <Switch
                  label="Enable PayPal"
                  checked={form.payments.paypal.enabled}
                  onChange={(e) => setField('payments', 'paypal', { ...form.payments.paypal, enabled: e.target.checked })}
                />
                <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <Select
                    label="Environment"
                    value={form.payments.paypal.mode}
                    onChange={(e) => setField('payments', 'paypal', { ...form.payments.paypal, mode: e.target.value })}
                  >
                    <option value="sandbox">Sandbox (Test)</option>
                    <option value="live">Live (Production)</option>
                  </Select>
                  <Input
                    label="Client ID"
                    value={form.payments.paypal.clientId}
                    onChange={(e) => setField('payments', 'paypal', { ...form.payments.paypal, clientId: e.target.value })}
                    placeholder="A...z"
                  />
                  <Input
                    label="Client Secret"
                    type="password"
                    value={form.payments.paypal.clientSecret}
                    onChange={(e) => setField('payments', 'paypal', { ...form.payments.paypal, clientSecret: e.target.value })}
                    placeholder="EL...u"
                  />
                </div>
              </section>
            </CardContent>
          </Card>

          {/* Email/SMTP */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Mail className="h-5 w-5 text-primary" aria-hidden="true" />
                Email (SMTP)
              </CardTitle>
              <CardDescription>Transactional emails (welcome, order confirmations, password resets).</CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <Switch
                  label="Enable SMTP"
                  checked={form.smtp.enabled}
                  onChange={(e) => setField('smtp', 'enabled', e.target.checked)}
                />
              </div>
              <Input
                label="Host"
                value={form.smtp.host}
                onChange={(e) => setField('smtp', 'host', e.target.value)}
                placeholder="smtp.example.com"
              />
              <Input
                label="Port"
                type="number"
                value={form.smtp.port}
                onChange={(e) => setField('smtp', 'port', Number(e.target.value))}
                placeholder="587"
              />
              <Input
                label="Username"
                autoComplete="off"
                value={form.smtp.user}
                onChange={(e) => setField('smtp', 'user', e.target.value)}
                placeholder="user@example.com"
              />
              <Input
                label="Password"
                type="password"
                autoComplete="new-password"
                value={form.smtp.pass}
                onChange={(e) => setField('smtp', 'pass', e.target.value)}
                placeholder={savedKeys ? '•••••••• (kept)' : 'SMTP password'}
              />
              <Input
                label="From Name"
                value={form.smtp.fromName}
                onChange={(e) => setField('smtp', 'fromName', e.target.value)}
                placeholder="Acme Support"
              />
              <Input
                label="From Email"
                type="email"
                value={form.smtp.fromEmail}
                onChange={(e) => setField('smtp', 'fromEmail', e.target.value)}
                placeholder="no-reply@example.com"
              />
              <div className="sm:col-span-2">
                <Switch
                  label="Secure connection (TLS/SSL)"
                  checked={form.smtp.secure}
                  onChange={(e) => setField('smtp', 'secure', e.target.checked)}
                />
              </div>
            </CardContent>
          </Card>

          {/* Currency */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Coins className="h-5 w-5 text-primary" aria-hidden="true" />
                Base Currency
              </CardTitle>
              <CardDescription>Used across prices, invoices and analytics.</CardDescription>
            </CardHeader>
            <CardContent>
              <Select
                label="Currency"
                value={form.currency.code}
                onChange={(e) => setField('currency', 'code', e.target.value)}
              >
                {currencies}
              </Select>
            </CardContent>
          </Card>

          <div className="flex items-center justify-end gap-3">
            <ShieldAlert className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
            <span className="text-xs text-muted-foreground">Changes apply instantly — no restart needed.</span>
            <Button type="submit" disabled={saving} leftIcon={Save}>
              {saving ? 'Saving…' : 'Save Settings'}
            </Button>
          </div>
        </form>
      )}
    </div>
  );
}