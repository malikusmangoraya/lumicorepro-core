'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Field, Input } from '@/components/ui/field';

export function LoginForm({ next = '/account' }: { next?: string }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;
    setPending(true);
    setError(null);

    const form = new FormData(event.currentTarget);
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: String(form.get('email') ?? ''),
          password: String(form.get('password') ?? ''),
          remember: form.get('remember') === 'on',
        }),
      });
      const body = (await response.json()) as { success: boolean; message?: string };

      if (!response.ok || !body.success) {
        setError(body.message ?? 'Those details did not match an account.');
        setPending(false);
        return;
      }

      router.replace(next);
      router.refresh();
    } catch {
      setError('Network error. Please try again.');
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4" noValidate>
      <Field id="login-email" label="Email">
        <Input
          id="login-email"
          name="email"
          type="email"
          required
          autoComplete="email"
          placeholder="you@example.com"
        />
      </Field>

      <Field id="login-password" label="Password">
        <Input
          id="login-password"
          name="password"
          type="password"
          required
          autoComplete="current-password"
          placeholder="••••••••"
        />
      </Field>

      <label className="flex items-center gap-2 text-sm text-muted">
        <input
          type="checkbox"
          name="remember"
          className="size-4 rounded border-line bg-canvas accent-primary"
        />
        Keep me signed in
      </label>

      {error && (
        <p role="alert" className="text-sm font-medium text-red-400">
          {error}
        </p>
      )}

      <Button type="submit" fullWidth disabled={pending}>
        {pending ? (
          <>
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
            Signing in…
          </>
        ) : (
          'Sign in'
        )}
      </Button>
    </form>
  );
}

export function RegisterForm() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;
    setPending(true);
    setError(null);

    const form = new FormData(event.currentTarget);
    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: String(form.get('name') ?? ''),
          email: String(form.get('email') ?? ''),
          password: String(form.get('password') ?? ''),
        }),
      });
      const body = (await response.json()) as {
        success: boolean;
        message?: string;
        details?: { fieldErrors?: Record<string, string[]> };
      };

      if (!response.ok || !body.success) {
        const first = body.details?.fieldErrors
          ? Object.values(body.details.fieldErrors)[0]?.[0]
          : undefined;
        setError(first ?? body.message ?? 'Could not create the account.');
        setPending(false);
        return;
      }

      router.replace('/account');
      router.refresh();
    } catch {
      setError('Network error. Please try again.');
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4" noValidate>
      <Field id="register-name" label="Name">
        <Input id="register-name" name="name" required minLength={2} autoComplete="name" />
      </Field>
      <Field id="register-email" label="Email">
        <Input id="register-email" name="email" type="email" required autoComplete="email" />
      </Field>
      <Field id="register-password" label="Password" hint="8+ characters, letter and number">
        <Input
          id="register-password"
          name="password"
          type="password"
          required
          minLength={8}
          autoComplete="new-password"
        />
      </Field>

      <label className="flex items-start gap-2 text-sm text-muted">
        <input
          type="checkbox"
          required
          className="mt-0.5 size-4 rounded border-line bg-canvas accent-primary"
        />
        <span>
          I agree to the{' '}
          <a href="/terms" className="text-accent hover:underline">
            terms
          </a>{' '}
          and{' '}
          <a href="/privacy" className="text-accent hover:underline">
            privacy policy
          </a>
          .
        </span>
      </label>

      {error && (
        <p role="alert" className="text-sm font-medium text-red-400">
          {error}
        </p>
      )}

      <Button type="submit" fullWidth disabled={pending}>
        {pending ? (
          <>
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
            Creating account…
          </>
        ) : (
          'Create account'
        )}
      </Button>
    </form>
  );
}

export function SignOutButton() {
  const router = useRouter();
  const [pending, setPending] = useState(false);

  return (
    <Button
      variant="outline"
      size="sm"
      disabled={pending}
      onClick={async () => {
        setPending(true);
        await fetch('/api/auth/logout', { method: 'POST' });
        router.replace('/');
        router.refresh();
      }}
    >
      {pending ? 'Signing out…' : 'Sign out'}
    </Button>
  );
}
