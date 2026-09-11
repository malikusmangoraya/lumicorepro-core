import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { Card, Button, Alert } from '@/components/ui';

export default function VerifyEmailPage() {
  const { token = '' } = useParams();
  const { verifyEmail, resendVerification } = useAuth();
  const [status, setStatus] = useState('loading'); // loading | success | error
  const [message, setMessage] = useState('');

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const data = await verifyEmail(token);
        if (active) {
          setStatus('success');
          setMessage(data?.message || 'Email verified successfully');
        }
      } catch (err) {
        if (active) {
          setStatus('error');
          setMessage(err.response?.data?.error || err.message || 'Verification link is invalid or expired');
        }
      }
    })();
    return () => {
      active = false;
    };
  }, [token, verifyEmail]);

  const handleResend = async () => {
    const email = window.prompt('Enter your account email to resend verification:');
    if (!email) return;
    try {
      await resendVerification(email.trim());
      setMessage('If an account exists, a new verification link has been sent.');
    } catch (err) {
      setMessage(err.response?.data?.error || err.message || 'Could not resend verification email');
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center -mx-4 -my-8 px-4 py-12">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_top,hsl(var(--primary)/0.08),transparent_60%)]" />

      <div className="relative w-full max-w-sm animate-fade-in-up">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center h-14 w-14 rounded-2xl bg-primary/15 border border-primary/30 mb-3 animate-glow-pulse">
            {status === 'success' ? (
              <CheckCircle2 className="h-7 w-7 text-primary" />
            ) : status === 'error' ? (
              <XCircle className="h-7 w-7 text-destructive" />
            ) : (
              <Loader2 className="h-7 w-7 text-primary animate-spin" />
            )}
          </div>
          <h1 className="font-display text-2xl font-bold">
            {status === 'loading'
              ? 'Verifying your email'
              : status === 'success'
                ? 'Email verified'
                : 'Verification failed'}
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {status === 'success'
              ? 'Your account is now fully secure.'
              : status === 'error'
                ? 'This link may be invalid or expired.'
                : 'Please wait a moment...'}
          </p>
        </div>

        <Card animate="fade-up">
          <div className="space-y-4">
            {status !== 'loading' && (
              <Alert variant={status === 'success' ? 'success' : 'danger'}>{message}</Alert>
            )}

            {status === 'success' && (
              <div className="flex justify-center">
                <Link to="/login">
                  <Button variant="primary">Continue to Sign In</Button>
                </Link>
              </div>
            )}

            {status === 'error' && (
              <div className="flex justify-center">
                <Button variant="outline" onClick={handleResend}>
                  Resend verification email
                </Button>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}