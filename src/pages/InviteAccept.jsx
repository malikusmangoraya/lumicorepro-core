import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../components/common/ThemeProvider';
import { inviteAPI } from '../services/api';
import {
  AlertCircle,
  Users,
  Loader2,
  Eye,
  EyeOff,
  Lock,
  Globe,
} from 'lucide-react';

export default function InviteAccept() {
  const { t } = useTranslation();
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const { token } = useParams();

  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const { data, isLoading, isError } = useQuery({
    queryKey: ['invite', token],
    queryFn: () => inviteAPI.resolve(token),
    retry: false,
  });

  const invite = data?.data?.data;

  const acceptMutation = useMutation({
    mutationFn: () => inviteAPI.accept(token, { name, password }),
    onSuccess: (res) => {
      const tokenData = res?.data?.token;
      if (tokenData) {
        localStorage.setItem('token', tokenData);
      }
      window.location.href = '/dashboard';
    },
  });

  const inputClass = 'w-full bg-background border border-border rounded-lg px-3 py-2 text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary transition-colors';
  const labelClass = 'text-sm font-medium text-muted-foreground mb-1 block';

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-12">
            <Loader2 className="h-8 w-8 text-primary animate-spin" aria-hidden="true" />
            <p className="text-sm text-muted-foreground mt-3">
              {t('invite.loading', 'Loading invitation...')}
            </p>
          </div>
        )}

        {isError && (
          <div className="bg-card rounded-xl border border-border shadow-sm p-8 text-center">
            <AlertCircle className="h-10 w-10 text-destructive mx-auto mb-4" aria-hidden="true" />
            <h2 className="text-lg font-semibold text-foreground mb-2">
              {t('invite.invalidTitle', 'Invalid Invitation')}
            </h2>
            <p className="text-sm text-muted-foreground mb-6">
              {t('invite.invalidMessage', 'This invite has expired or is invalid.')}
            </p>
            <Link
              to="/register"
              className="inline-flex items-center gap-1 px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
            >
              {t('invite.register', 'Create Account')}
            </Link>
          </div>
        )}

        {invite && (
          <div className="bg-card rounded-xl border border-border shadow-sm p-6">
            <div className="text-center mb-6">
              <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-3">
                <Users className="h-6 w-6 text-primary" aria-hidden="true" />
              </div>
              <h2 className="text-lg font-semibold text-foreground">
                {t('invite.title', 'You\'re Invited!')}
              </h2>
            </div>

            <div className="bg-background rounded-lg border border-border p-4 mb-6 space-y-3">
              <div className="flex items-center gap-2 text-sm">
                <Globe className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                <span className="text-muted-foreground">
                  {t('invite.org', 'Organization')}:
                </span>
                <span className="text-foreground font-medium">{invite.orgName}</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Lock className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                <span className="text-muted-foreground">
                  {t('invite.email', 'Email')}:
                </span>
                <span className="text-foreground font-medium">{invite.email}</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Users className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                <span className="text-muted-foreground">
                  {t('invite.role', 'Role')}:
                </span>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary capitalize">
                  {invite.role}
                </span>
              </div>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                acceptMutation.mutate();
              }}
            >
              <div className="space-y-4 mb-6">
                <div>
                  <label className={labelClass}>
                    {t('invite.name', 'Your Name')}
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder={t('invite.namePlaceholder', 'John Doe')}
                    className={inputClass}
                    required
                  />
                </div>

                <div>
                  <label className={labelClass}>
                    {t('invite.password', 'Password')}
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder={t('invite.passwordPlaceholder', 'Create a password')}
                      className={`${inputClass} pr-10`}
                      required
                      minLength={8}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((prev) => !prev)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      aria-label={showPassword ? t('invite.hidePassword', 'Hide password') : t('invite.showPassword', 'Show password')}
                    >
                      {showPassword ? (
                        <EyeOff className="h-4 w-4" aria-hidden="true" />
                      ) : (
                        <Eye className="h-4 w-4" aria-hidden="true" />
                      )}
                    </button>
                  </div>
                </div>
              </div>

              {acceptMutation.isError && (
                <div className="flex items-center gap-2 text-sm text-destructive mb-4 p-3 rounded-lg bg-destructive/10">
                  <AlertCircle className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
                  {acceptMutation.error?.response?.data?.message ||
                    t('invite.error', 'Something went wrong. Please try again.')}
                </div>
              )}

              <button
                type="submit"
                disabled={acceptMutation.isPending}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                {acceptMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                ) : (
                  <Users className="h-4 w-4" aria-hidden="true" />
                )}
                {t('invite.join', 'Confirm & Join')}
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
