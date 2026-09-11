import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, User, ArrowRight, Sparkles, Check } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useAppContext } from '@/context/AppContext';
import { Card, Input, Button, Alert, Progress } from '@/components/ui';

const STRENGTH_LEVELS = [
  { label: 'Weak', score: 1 },
  { label: 'Fair', score: 2 },
  { label: 'Good', score: 3 },
  { label: 'Strong', score: 4 },
];

const getPasswordStrength = (pwd) => {
  let score = 0;
  if (pwd.length >= 8) score++;
  if (/[A-Z]/.test(pwd)) score++;
  if (/[0-9]/.test(pwd)) score++;
  if (/[^A-Za-z0-9]/.test(pwd)) score++;
  return score;
};

const strengthVariant = (score) => {
  if (score <= 1) return 'danger';
  if (score === 2) return 'warning';
  if (score === 3) return 'info';
  return 'success';
};

export default function RegisterPage() {
  const { register } = useAuth();
  const { addNotification } = useAppContext();
  const navigate = useNavigate();

  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '' });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [agreed, setAgreed] = useState(false);

  const strength = getPasswordStrength(form.password);
  const strengthLevel = STRENGTH_LEVELS[Math.min(strength - 1, 3)];

  const validate = () => {
    const e = {};
    if (!form.name.trim()) e.name = 'Full name is required';
    if (!form.email) e.email = 'Email is required';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = 'Enter a valid email';
    if (!form.password) e.password = 'Password is required';
    else if (form.password.length < 6) e.password = 'Must be at least 6 characters';
    if (!form.confirm) e.confirm = 'Please confirm your password';
    else if (form.confirm !== form.password) e.confirm = 'Passwords do not match';
    if (!agreed) e.agreed = 'You must accept the terms';
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
      await register({ name: form.name.trim(), email: form.email.trim(), password: form.password });
      addNotification('Account created successfully! Welcome to LumiCorePro.', 'success');
      navigate('/');
    } catch (err) {
      setErrors({
        general:
          err.response?.data?.error || err.message || 'Registration failed. Please try again.',
      });
    } finally {
      setLoading(false);
    }
  };

  const change = (field) => (e) => {
    setForm((f) => ({ ...f, [field]: e.target.value }));
    if (errors[field] || errors.general) setErrors((er) => ({ ...er, [field]: '', general: '' }));
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center -mx-4 -my-8 px-4 py-12">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_top,hsl(var(--primary)/0.08),transparent_60%)]" />

      <div className="relative w-full max-w-sm animate-fade-in-up">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center h-14 w-14 rounded-2xl bg-primary/15 border border-primary/30 mb-3 animate-glow-pulse">
            <Sparkles className="h-7 w-7 text-primary" />
          </div>
          <h1 className="font-display text-2xl font-bold">Create an account</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Start building AI websites with LumiCorePro
          </p>
        </div>

        <Card animate="fade-up">
          {errors.general && (
            <Alert
              variant="danger"
              className="mb-4"
              dismissible
              onDismiss={() => setErrors((er) => ({ ...er, general: '' }))}
            >
              {errors.general}
            </Alert>
          )}

          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            <Input
              label="Full Name"
              value={form.name}
              onChange={change('name')}
              error={errors.name}
              placeholder="Sarah Connor"
              leftIcon={<User className="h-4 w-4" />}
              autoComplete="name"
              required
            />

            <Input
              label="Email Address"
              type="email"
              value={form.email}
              onChange={change('email')}
              error={errors.email}
              placeholder="sarah@example.com"
              leftIcon={<Mail className="h-4 w-4" />}
              autoComplete="email"
              required
            />

            <Input
              label="Password"
              type="password"
              value={form.password}
              onChange={change('password')}
              error={errors.password}
              placeholder="At least 6 characters"
              leftIcon={<Lock className="h-4 w-4" />}
              autoComplete="new-password"
              required
            />

            {form.password && (
              <div className="space-y-1.5">
                <div className="flex justify-between text-[11px] text-muted-foreground">
                  <span>Strength</span>
                  <span className="font-medium">{strengthLevel?.label || 'Weak'}</span>
                </div>
                <Progress
                  value={strength * 25}
                  variant={strengthVariant(strength)}
                  size="xs"
                  showLabel={false}
                />
              </div>
            )}

            <Input
              label="Confirm Password"
              type="password"
              value={form.confirm}
              onChange={change('confirm')}
              error={errors.confirm}
              placeholder="Repeat password"
              leftIcon={<Lock className="h-4 w-4" />}
              rightIcon={
                form.confirm && form.confirm === form.password ? (
                  <Check className="h-4 w-4 text-emerald-400" />
                ) : undefined
              }
              autoComplete="new-password"
              required
            />

            <div>
              <label className="flex cursor-pointer items-start gap-2.5 group">
                <input
                  type="checkbox"
                  checked={agreed}
                  onChange={(e) => {
                    setAgreed(e.target.checked);
                    if (errors.agreed) setErrors((er) => ({ ...er, agreed: '' }));
                  }}
                  className="mt-0.5 h-4 w-4 shrink-0 rounded border-border accent-primary"
                />
                <span className="text-xs leading-relaxed text-muted-foreground">
                  I agree to the{' '}
                  <Link to="/terms" className="text-primary hover:underline">
                    Terms of Service
                  </Link>{' '}
                  and{' '}
                  <Link to="/privacy" className="text-primary hover:underline">
                    Privacy Policy
                  </Link>
                </span>
              </label>
              {errors.agreed && <p className="mt-1 text-xs text-destructive">{errors.agreed}</p>}
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              fullWidth
              loading={loading}
              rightIcon={<ArrowRight className="h-4 w-4" />}
            >
              Create Account
            </Button>
          </form>
        </Card>

        <p className="mt-5 text-center text-sm text-muted-foreground">
          Already have an account?{' '}
          <Link to="/login" className="font-semibold text-primary hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
