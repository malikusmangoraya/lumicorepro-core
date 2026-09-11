import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Lock, KeyRound, ArrowRight } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { Card, Input, Button, Alert } from '@/components/ui';

export default function ResetPasswordPage() {
  const { token = '' } = useParams();
  const { resetPassword } = useAuth();
  const [form, setForm] = useState({ password: '', confirm: '' });
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(false);

  const validate = () => {
    if (form.password.length < 6) return 'Password must be at least 6 characters';
    if (form.password !== form.confirm) return 'Passwords do not match';
    return '';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const err = validate();
    if (err) {
      setError(err);
      return;
    }
    setError('');
    setLoading(true);
    try {
      await resetPassword(token, form.password);
      setDone(true);
    } catch (err2) {
      setError(
        err2.response?.data?.error || err2.message || 'Reset failed. The link may be expired.'
      );
    } finally {
      setLoading(false);
    }
  };

  const change = (field) => (e) => {
    setForm((f) => ({ ...f, [field]: e.target.value }));
    setError('');
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center -mx-4 -my-8 px-4 py-12">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_top,hsl(var(--primary)/0.08),transparent_60%)]" />

      <div className="relative w-full max-w-sm animate-fade-in-up">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center h-14 w-14 rounded-2xl bg-primary/15 border border-primary/30 mb-3 animate-glow-pulse">
            <KeyRound className="h-7 w-7 text-primary" />
          </div>
          <h1 className="font-display text-2xl font-bold">Reset password</h1>
          <p className="text-sm text-muted-foreground mt-1">Choose a strong new password</p>
        </div>

        <Card animate="fade-up">
          {done ? (
            <div className="space-y-4">
              <Alert variant="success">Password updated successfully. You can sign in now.</Alert>
              <div className="flex justify-center">
                <Link to="/login">
                  <Button variant="primary" rightIcon={<ArrowRight className="h-4 w-4" />}>
                    Go to Sign In
                  </Button>
                </Link>
              </div>
            </div>
          ) : (
            <>
              {!token && (
                <Alert variant="danger" className="mb-4">
                  Missing reset token. Use the link from your email.
                </Alert>
              )}
              <form onSubmit={handleSubmit} noValidate className="space-y-4">
                {error && (
                  <Alert variant="danger" dismissible onDismiss={() => setError('')}>
                    {error}
                  </Alert>
                )}
                <Input
                  label="New password"
                  type="password"
                  name="password"
                  value={form.password}
                  onChange={change('password')}
                  placeholder="••••••••"
                  autoComplete="new-password"
                  leftIcon={<Lock className="h-4 w-4" />}
                  error={error}
                />
                <Input
                  label="Confirm password"
                  type="password"
                  name="confirm"
                  value={form.confirm}
                  onChange={change('confirm')}
                  placeholder="••••••••"
                  autoComplete="new-password"
                  leftIcon={<Lock className="h-4 w-4" />}
                  error={error}
                />
                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  fullWidth
                  loading={loading}
                  disabled={!token}
                  rightIcon={<ArrowRight className="h-4 w-4" />}
                >
                  Update Password
                </Button>
              </form>
            </>
          )}
        </Card>

        <p className="mt-5 text-center text-sm text-muted-foreground">
          Remembered it?{' '}
          <Link to="/login" className="font-semibold text-primary hover:underline">
            Back to Sign In
          </Link>
        </p>
      </div>
    </div>
  );
}