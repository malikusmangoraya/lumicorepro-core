import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, ShieldCheck, ArrowRight } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { Card, Input, Button, Alert } from '@/components/ui';

export default function ChangePasswordPage() {
  const { changePassword, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ currentPassword: '', password: '', confirm: '' });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const validate = () => {
    if (!form.currentPassword) return 'Enter your current password';
    if (form.password.length < 6) return 'New password must be at least 6 characters';
    if (form.password !== form.confirm) return 'New passwords do not match';
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
      await changePassword({
        currentPassword: form.currentPassword,
        newPassword: form.password,
      });
      setSuccess(true);
    } catch (err2) {
      setError(
        err2.response?.data?.error || err2.message || 'Could not change password. Check your current password.'
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
            <ShieldCheck className="h-7 w-7 text-primary" />
          </div>
          <h1 className="font-display text-2xl font-bold">Change password</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Update the password used to sign in to your account
          </p>
        </div>

        <Card animate="fade-up">
          {success ? (
            <div className="space-y-4">
              <Alert variant="success">Password changed successfully.</Alert>
              <div className="flex justify-center">
                <Button variant="primary" onClick={() => navigate('/profile')} rightIcon={<ArrowRight className="h-4 w-4" />}>
                  Back to Profile
                </Button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} noValidate className="space-y-4">
              {!isAuthenticated && (
                <Alert variant="danger" className="mb-4">
                  You must be signed in to change your password.
                </Alert>
              )}
              {error && (
                <Alert variant="danger" dismissible onDismiss={() => setError('')}>
                  {error}
                </Alert>
              )}
              <Input
                label="Current password"
                type="password"
                name="currentPassword"
                value={form.currentPassword}
                onChange={change('currentPassword')}
                placeholder="••••••••"
                autoComplete="current-password"
                leftIcon={<Lock className="h-4 w-4" />}
                error={error}
              />
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
                label="Confirm new password"
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
                disabled={!isAuthenticated}
              >
                Update Password
              </Button>
            </form>
          )}
        </Card>
      </div>
    </div>
  );
}