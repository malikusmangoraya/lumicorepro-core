import { useEffect, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { useAppContext } from '@/context/AppContext';
import { Card, Button, Alert } from '@/components/ui';

export default function OAuthCallbackPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { login: appLogin } = useAppContext();
  const [status, setStatus] = useState('loading');
  const [message, setMessage] = useState('');
  const ran = useRef(false);

  useEffect(() => {
    if (ran.current) return;
    ran.current = true;

    const error = params.get('error');
    const token = params.get('token');
    const rawUser = params.get('user');

    if (error) {
      setStatus('error');
      setMessage(decodeURIComponent(error));
      return;
    }

    if (token) {
      let user = null;
      if (rawUser) {
        try {
          user = JSON.parse(rawUser);
        } catch {
          user = null;
        }
      }
      if (user?.email) {
        appLogin(user, token);
        setStatus('success');
        setMessage('Signed in successfully.');
        window.setTimeout(() => navigate('/'), 1200);
        return;
      }
    }

    setStatus('error');
    setMessage(
      'OAuth callback missing required data. Please try the standard sign-in flow instead.'
    );
  }, [params, appLogin, navigate]);

  return (
    <div className="min-h-[80vh] flex items-center justify-center -mx-4 -my-8 px-4 py-12">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_top,hsl(var(--primary)/0.08),transparent_60%)]" />

      <div className="relative w-full max-w-sm animate-fade-in-up">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center h-14 w-14 rounded-2xl bg-primary/15 border border-primary/30 mb-3">
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
              ? 'Completing sign in'
              : status === 'success'
                ? 'Signed in'
                : 'Authentication error'}
          </h1>
        </div>

        <Card animate="fade-up">
          {status === 'error' && (
            <div className="space-y-4">
              <Alert variant="danger">{message}</Alert>
              <div className="flex justify-center">
                <Button variant="primary" onClick={() => navigate('/login')}>
                  Go to Sign In
                </Button>
              </div>
            </div>
          )}
          {status === 'success' && <Alert variant="success">{message}</Alert>}
        </Card>
      </div>
    </div>
  );
}