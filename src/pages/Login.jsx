import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, ArrowRight, Sparkles, ShieldCheck } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useAppContext } from '@/context/AppContext';
import authService from '@/services/auth';
import { Card, Input, Button, Alert, Divider, Modal } from '@/components/ui';
import PageSEO from '@/components/common/PageSEO';
import Turnstile from '@/components/common/CaptchaTurnstile';

const TURNSTILE_SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY || '';

export default function LoginPage() {
  const { login, verify2FALogin } = useAuth();
  const { addNotification, login: appLogin } = useAppContext();
  const navigate = useNavigate();

  const [form, setForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [forgotModal, setForgotModal] = useState(false);
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotStatus, setForgotStatus] = useState(null);
  const [twoFAStep, setTwoFAStep] = useState(false);
  const [twoFATarget, setTwoFATarget] = useState('');
  const [otp, setOtp] = useState('');
  const [otpError, setOtpError] = useState('');
  const [captchaToken, setCaptchaToken] = useState(null);

  const validate = () => {
    const e = {};
    if (!form.email) e.email = 'Email is required';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = 'Enter a valid email';
    if (!form.password) e.password = 'Password is required';
    else if (form.password.length < 6) e.password = 'Password must be at least 6 characters';
    return e;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) {
      setErrors(errs);
      return;
    }
    setErrors({});
    setLoading(true);
    try {
      const res = await login({ email: form.email.trim(), password: form.password, captchaToken });
      if (res?.requires2FA) {
        setTwoFAStep(true);
        setTwoFATarget(res.user?.email || form.email.trim());
        addNotification('Two-Factor Authentication is required for this account.', 'info');
        return;
      }
      navigate('/');
    } catch (err) {
      setErrors({
        general:
          err.response?.data?.error ||
          err.message ||
          'Login failed. Check your email and password.',
      });
    } finally {
      setLoading(false);
    }
  };

  const handle2FASubmit = async (e) => {
    e.preventDefault();
    const code = otp.trim();
    if (!/^\d{6}$/.test(code)) {
      setOtpError('Enter the 6-digit code');
      return;
    }
    setOtpError('');
    setLoading(true);
    try {
      const data = await verify2FALogin({ email: twoFATarget, otp: code });
      if (data?.token && data?.user) {
        appLogin(data.user, data.token);
        addNotification('2FA verified — welcome back.', 'success');
        navigate('/');
        return;
      }
      setOtpError('Unexpected response from 2FA verification');
    } catch (err) {
      setOtpError(err.response?.data?.error || err.message || 'Invalid or expired 2FA code');
    } finally {
      setLoading(false);
    }
  };

  const change = (field) => (e) => {
    setForm((f) => ({ ...f, [field]: e.target.value }));
    if (errors[field] || errors.general) setErrors((er) => ({ ...er, [field]: '', general: '' }));
  };

  const fillDemo = (role = 'user') => {
    setForm(
      role === 'admin'
        ? { email: 'admin@example.com', password: 'Password123!' }
        : { email: 'demo@example.com', password: 'Password123!' }
    );
    setErrors({});
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    if (!forgotEmail || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(forgotEmail)) {
      setForgotStatus({ type: 'error', msg: 'Enter a valid email address' });
      return;
    }
    try {
      await authService.forgotPassword(forgotEmail);
    } catch {
      /* no-op */
    }
    setForgotStatus({
      type: 'success',
      msg: 'If an account exists, password reset instructions have been sent.',
    });
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center -mx-4 -my-8 px-4 py-12">
      <PageSEO
        title="Sign In — LumicorePro"
        description="Sign in to LumicorePro to generate AI-powered websites with the full 15-phase pipeline."
        noIndex
      />
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_top,hsl(var(--primary)/0.08),transparent_60%)]" />

      <div className="relative w-full max-w-sm animate-fade-in-up">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center h-14 w-14 rounded-2xl bg-primary/15 border border-primary/30 mb-3 animate-glow-pulse">
            <Sparkles className="h-7 w-7 text-primary" />
          </div>
          <h1 className="font-display text-2xl font-bold">Welcome back</h1>
          <p className="text-sm text-muted-foreground mt-1">Sign in to your LumicorePro account</p>
        </div>

        <Card animate="fade-up">
          <div className="mb-4 flex items-center justify-between rounded-xl border border-primary/20 bg-primary/5 p-2.5 text-xs">
            <span className="flex items-center gap-1.5 font-medium text-muted-foreground">
              <ShieldCheck className="h-3.5 w-3.5 text-primary" /> Quick demo:
            </span>
            <div className="flex gap-2">
              <Button variant="ghost" size="xs" onClick={() => fillDemo('user')}>
                Demo User
              </Button>
              <Button variant="ghost" size="xs" onClick={() => fillDemo('admin')}>
                Admin
              </Button>
            </div>
          </div>

          {errors.general && !twoFAStep && (
            <Alert
              variant="danger"
              className="mb-4"
              dismissible
              onDismiss={() => setErrors((er) => ({ ...er, general: '' }))}
            >
              {errors.general}
            </Alert>
          )}

          {twoFAStep ? (
            <form onSubmit={handle2FASubmit} noValidate className="space-y-4">
              <p className="text-xs text-muted-foreground">
                A 6-digit code was sent to{' '}
                <span className="font-medium text-foreground">{twoFATarget}</span>.
              </p>
              {otpError && (
                <Alert variant="danger" dismissible onDismiss={() => setOtpError('')}>
                  {otpError}
                </Alert>
              )}
              <Input
                label="Verification code"
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={6}
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="000000"
                autoComplete="one-time-code"
                leftIcon={<ShieldCheck className="h-4 w-4" />}
                error={otpError}
              />
              <Button type="submit" variant="primary" size="lg" fullWidth loading={loading}>
                Verify &amp; Sign In
              </Button>
              <Button
                variant="ghost"
                size="sm"
                fullWidth
                onClick={() => {
                  setTwoFAStep(false);
                  setOtp('');
                  setOtpError('');
                }}
              >
                Back to sign in
              </Button>
            </form>
          ) : (
          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            <Input
              label="Email"
              type="email"
              name="email"
              value={form.email}
              onChange={change('email')}
              placeholder="you@example.com"
              autoComplete="email"
              leftIcon={<Mail className="h-4 w-4" />}
              error={errors.email}
            />

            <div>
              <div className="mb-1.5 flex items-center justify-between">
                <label className="text-sm font-medium text-foreground" htmlFor="password">
                  Password
                </label>
                <Button
                  variant="link"
                  size="xs"
                  type="button"
                  onClick={() => {
                    setForgotModal(true);
                    setForgotEmail(form.email);
                    setForgotStatus(null);
                  }}
                >
                  Forgot password?
                </Button>
              </div>
              <Input
                id="password"
                type="password"
                name="password"
                value={form.password}
                onChange={change('password')}
                placeholder="••••••••"
                autoComplete="current-password"
                leftIcon={<Lock className="h-4 w-4" />}
                error={errors.password}
              />
            </div>

            {TURNSTILE_SITE_KEY && !twoFAStep && (
              <div>
                <Turnstile
                  siteKey={TURNSTILE_SITE_KEY}
                  onVerify={(token) => {
                    setCaptchaToken(token);
                    if (errors.captcha) setErrors((er) => ({ ...er, captcha: '' }));
                  }}
                />
                {errors.captcha && (
                  <p className="mt-1 text-xs text-destructive" role="alert">
                    {errors.captcha}
                  </p>
                )}
              </div>
            )}

            <Button
              type="submit"
              variant="primary"
              size="lg"
              fullWidth
              loading={loading}
              rightIcon={<ArrowRight className="h-4 w-4" />}
            >
              Sign In
            </Button>
          </form>
          )}

          {!twoFAStep && (
            <>
              <Divider label="or continue with" className="my-5" />

              <div className="grid grid-cols-2 gap-3">
                {['GitHub', 'Google'].map((label) => (
                  <Button
                    key={label}
                    variant="outline"
                    onClick={() =>
                      addNotification(
                        `${label} OAuth login is ready to configure in production settings`,
                        'info'
                      )
                    }
                  >
                    {label === 'GitHub' ? '⚡' : '🌐'} {label}
                  </Button>
                ))}
              </div>
            </>
          )}
        </Card>

        <p className="mt-5 text-center text-sm text-muted-foreground">
          Don't have an account?{' '}
          <Link to="/register" className="font-semibold text-primary hover:underline">
            Create one free
          </Link>
        </p>
      </div>

      <Modal
        open={forgotModal}
        onClose={() => setForgotModal(false)}
        title="Reset Password"
        size="sm"
      >
        <p className="text-xs text-muted-foreground">
          Enter your account email and we will send password reset instructions.
        </p>
        {forgotStatus && (
          <Alert variant={forgotStatus.type === 'success' ? 'success' : 'danger'} className="mt-3">
            {forgotStatus.msg}
          </Alert>
        )}
        <form onSubmit={handleForgotPassword} className="mt-4 space-y-4">
          <Input
            type="email"
            value={forgotEmail}
            onChange={(e) => setForgotEmail(e.target.value)}
            placeholder="you@example.com"
            label="Account Email"
            required
          />
          <div className="flex justify-end gap-2">
            <Button variant="outline" size="sm" onClick={() => setForgotModal(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm">
              Send Link
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
