import React, { useState } from 'react';
import { Eye, EyeOff, Lock, Mail, User, UserPlus, ShieldCheck } from 'lucide-react';
import { cn } from '../../utils';
import Spinner from '../ui/Spinner';

const PASSWORD_STRENGTH = [
  { label: 'Weak', color: 'bg-destructive', min: 0 },
  { label: 'Fair', color: 'bg-amber-500', min: 4 },
  { label: 'Good', color: 'bg-sky-500', min: 7 },
  { label: 'Strong', color: 'bg-green-600', min: 10 },
];

const strengthFor = (password) => {
  let score = 0;
  if (password.length >= 8) score += 3;
  if (password.length >= 12) score += 3;
  if (/[A-Z]/.test(password)) score += 2;
  if (/\d/.test(password)) score += 1;
  if (/[^A-Za-z0-9]/.test(password)) score += 1;
  return Math.min(score, PASSWORD_STRENGTH.length - 1);
};

const RegisterForm = ({
  onSubmit,
  onLogin,
  title = 'Create an account',
  subtitle = 'Join us — it takes less than a minute',
  submitLabel = 'Create account',
  className = '',
  error = '',
}) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [agree, setAgree] = useState(false);
  const [loading, setLoading] = useState(false);

  const strength = strengthFor(password);
  const meter = PASSWORD_STRENGTH[strength];
  const mismatch = confirm.length > 0 && confirm !== password;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (mismatch) return;
    setLoading(true);
    try {
      if (typeof onSubmit === 'function') {
        await onSubmit({ name, email, password });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className={cn('w-full max-w-md space-y-5', className)} noValidate>
      <div className="space-y-1.5">
        <h2 className="text-2xl font-bold tracking-tight text-foreground">{title}</h2>
        <p className="text-sm text-muted-foreground">{subtitle}</p>
      </div>

      <div className="space-y-1.5">
        <label htmlFor="reg-name" className="text-sm font-medium text-foreground">
          Full name
        </label>
        <div className="relative">
          <User
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden="true"
          />
          <input
            id="reg-name"
            type="text"
            required
            autoComplete="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Jane Cooper"
            className="w-full rounded-lg border bg-background py-2.5 pl-10 pr-3 text-sm text-foreground outline-none transition-all duration-200 focus:border-primary focus:ring-2 focus:ring-primary/30"
          />
        </div>
      </div>

      <div className="space-y-1.5">
        <label htmlFor="reg-email" className="text-sm font-medium text-foreground">
          Email
        </label>
        <div className="relative">
          <Mail
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden="true"
          />
          <input
            id="reg-email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
            className="w-full rounded-lg border bg-background py-2.5 pl-10 pr-3 text-sm text-foreground outline-none transition-all duration-200 focus:border-primary focus:ring-2 focus:ring-primary/30"
          />
        </div>
      </div>

      <div className="space-y-1.5">
        <label htmlFor="reg-password" className="text-sm font-medium text-foreground">
          Password
        </label>
        <div className="relative">
          <Lock
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden="true"
          />
          <input
            id="reg-password"
            type={showPassword ? 'text' : 'password'}
            required
            minLength={8}
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="At least 8 characters"
            className="w-full rounded-lg border bg-background py-2.5 pl-10 pr-10 text-sm text-foreground outline-none transition-all duration-200 focus:border-primary focus:ring-2 focus:ring-primary/30"
          />
          <button
            type="button"
            onClick={() => setShowPassword((v) => !v)}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground transition-colors hover:text-foreground"
          >
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
        {password && (
          <div className="pt-1" aria-label={`Password strength: ${meter.label}`}>
            <div className="flex h-1.5 w-full gap-1 overflow-hidden rounded-full bg-muted">
              {PASSWORD_STRENGTH.map((level, i) => (
                <span
                  key={level.label}
                  className={cn(
                    'h-full flex-1 rounded-full transition-all duration-200',
                    i <= strength ? level.color : 'bg-muted'
                  )}
                />
              ))}
            </div>
            <p className="mt-1 text-xs text-muted-foreground">Strength: {meter.label}</p>
          </div>
        )}
      </div>

      <div className="space-y-1.5">
        <label htmlFor="reg-confirm" className="text-sm font-medium text-foreground">
          Confirm password
        </label>
        <input
          id="reg-confirm"
          type={showPassword ? 'text' : 'password'}
          required
          autoComplete="new-password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          placeholder="Repeat your password"
          aria-invalid={mismatch}
          aria-describedby={mismatch ? 'reg-confirm-msg' : undefined}
          className={cn(
            'w-full rounded-lg border bg-background py-2.5 pl-10 pr-3 text-sm text-foreground outline-none transition-all duration-200 focus:border-primary focus:ring-2 focus:ring-primary/30',
            mismatch && 'border-destructive focus:border-destructive focus:ring-destructive/30'
          )}
        />
        {mismatch && (
          <p id="reg-confirm-msg" role="alert" className="text-xs text-destructive">
            Passwords do not match.
          </p>
        )}
      </div>

      <label className="flex items-start gap-2 text-sm text-muted-foreground">
        <input
          type="checkbox"
          checked={agree}
          onChange={(e) => setAgree(e.target.checked)}
          required
          className="mt-0.5 h-4 w-4 rounded border-border accent-primary"
        />
        <span>
          I agree to the <span className="text-primary underline">Terms</span> and{' '}
          <span className="text-primary underline">Privacy Policy</span>.
        </span>
      </label>

      {error && (
        <p
          role="alert"
          className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={loading || (confirm.length > 0 && mismatch)}
        className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition-all duration-200 hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/40 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? (
          <Spinner size="sm" color="white" />
        ) : (
          <UserPlus className="h-4 w-4" aria-hidden="true" />
        )}
        {submitLabel}
      </button>

      {typeof onLogin === 'function' && (
        <p className="text-center text-sm text-muted-foreground">
          Already have an account?{' '}
          <button
            type="button"
            onClick={onLogin}
            className="font-medium text-primary hover:underline"
          >
            Sign in
          </button>
        </p>
      )}

      <p className="flex items-center justify-center gap-1.5 text-center text-xs text-muted-foreground">
        <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
        Protected by encrypted, rate-limited authentication.
      </p>
    </form>
  );
};

export default RegisterForm;
