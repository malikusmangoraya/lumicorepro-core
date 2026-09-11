import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, ArrowRight, ShieldCheck } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { Card, Input, Button, Alert } from '@/components/ui';

export default function ForgotPasswordPage() {
  const { forgotPassword } = useAuth();
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Enter a valid email address');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await forgotPassword(email.trim());
      setSent(true);
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Could not send reset email');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center -mx-4 -my-8 px-4 py-12">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_top,hsl(var(--primary)/0.08),transparent_60%)]" />

      <div className="relative w-full max-w-sm animate-fade-in-up">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center h-14 w-14 rounded-2xl bg-primary/15 border border-primary/30 mb-3 animate-glow-pulse">
            <ShieldCheck className="h-7 w-7 text-primary" />
          </div>
          <h1 className="font-display text-2xl font-bold">Forgot password</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Enter your account email to receive reset instructions
          </p>
        </div>

        <Card animate="fade-up">
          {sent ? (
            <div className="space-y-4">
              <Alert variant="success">
                If an account exists for that email, password reset instructions have been sent.
                The link expires in 15 minutes.
              </Alert>
              <div className="flex justify-center">
                <Link to="/login">
                  <Button variant="outline" rightIcon={<ArrowRight className="h-4 w-4" />}>
                    Back to Sign In
                  </Button>
                </Link>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} noValidate className="space-y-4">
              {error && (
                <Alert variant="danger" dismissible onDismiss={() => setError('')}>
                  {error}
                </Alert>
              )}
              <Input
                label="Email"
                type="email"
                name="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setError('');
                }}
                placeholder="you@example.com"
                autoComplete="email"
                leftIcon={<Mail className="h-4 w-4" />}
                error={error}
              />
              <Button
                type="submit"
                variant="primary"
                size="lg"
                fullWidth
                loading={loading}
                rightIcon={<ArrowRight className="h-4 w-4" />}
              >
                Send Reset Link
              </Button>
            </form>
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