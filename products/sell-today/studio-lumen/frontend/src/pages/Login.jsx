import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { Mail, Lock, Eye, ShieldCheck, ArrowRight, LoaderCircle } from 'lucide-react';
import api from '../services/api';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Login() {
  const { t } = useTranslation();
  const [show, setShow] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [remember, setRemember] = useState(false);

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <Navbar />

      {/* demo credentials for the live preview — remove before selling if you do not want them public */}
      <div className="mb-6 rounded-lg border border-[var(--t-border)] bg-surface p-4 text-sm">
        <p className="font-semibold" style={{ color: 'var(--t-heading)' }}>Demo access</p>
        <p className="text-slate-500 dark:text-slate-400">Demo accounts are seeded only when ENABLE_DEMO_SEED=true and DEMO_USER_PASSWORD is set (see backend/.env.example). Seeding is always disabled in production.</p>
      </div>
      <main id="main-content" className="flex-1 grid lg:grid-cols-2">
        <section
          className="relative hidden lg:flex flex-col justify-between p-12 text-white"
          style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
        >
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.3em] opacity-80">PHOTOGRAPHY</p>
            <h2 className="mt-6 text-4xl font-black leading-tight max-w-sm">Photography in pursuit of light.</h2>
            <p className="mt-4 max-w-sm text-white/85 leading-relaxed">Studio Lumen is a photographer\'s collective documenting architecture, people and wilderness in the warmest hour of the day.</p>
          </div>
          <ul className="space-y-3 text-sm">
            <li className="flex items-center gap-2"><ShieldCheck className="h-4 w-4" /> Secure, encrypted sign-in</li>
            <li className="flex items-center gap-2"><ShieldCheck className="h-4 w-4" /> Your data stays yours</li>
          </ul>
        </section>

        <section className="flex items-center justify-center px-6 py-16">
          <div className="w-full max-w-md" data-reveal>
            <h1 className="text-3xl font-extrabold tracking-tight" style={{ color: 'var(--t-heading)' }}>
              Welcome back to Studio Lumen
            </h1>
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
              Sign in to continue to your account.
            </p>

            <form onSubmit={async (e) => {
              e.preventDefault();
              setError('');
              if (!email || !password) { setError(t('Login.email_and_password_required', 'Email and password are required.')); return; }
              setLoading(true);
              try {
                const res = await api.post('/auth/login', { email, password, remember });
                if (res.data?.success) {
                  localStorage.setItem('auth_token', res.data.data?.accessToken || '');
                  localStorage.setItem('refresh_token', res.data.data?.refreshToken || '');
                  window.location.href = '/account';
                } else {
                  setError(res.data?.message || t('Login.invalid_credentials', 'Invalid email or password.'));
                }
              } catch (err) {
                setError(err.response?.data?.message || t('Login.login_failed', 'Login failed. Please try again.'));
              } finally {
                setLoading(false);
              }
            }} className="mt-8 space-y-5">
              <div>
                <label htmlFor="email" className="mb-1.5 block text-sm font-medium" style={{ color: 'var(--t-heading)' }}>
                  Email address
                </label>
                <div className="relative">
                  <Mail className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <input
                    id="email" name="email" type="email" required autoComplete="email"
                    placeholder="you@studio-lumen.test"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full rounded-xl border border-[var(--t-border)] bg-surface py-3 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--t-primary)]"
                  />
                </div>
              </div>

              <div>
                <div className="mb-1.5 flex items-center justify-between">
                  <label htmlFor="password" className="block text-sm font-medium" style={{ color: 'var(--t-heading)' }}>
                    Password
                  </label>
                  <Link to="/contact" className="text-xs font-semibold text-primary">{t('Login.forgot_password', t('Login.forgot_password', 'Forgot password?'))}</Link>
                </div>
                <div className="relative">
                  <Lock className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <input
                    id="password" name="password" type={show ? 'text' : 'password'} required autoComplete="current-password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full rounded-xl border border-[var(--t-border)] bg-surface py-3 pl-10 pr-16 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--t-primary)]"
                  />
                  <button
                    type="button"
                    onClick={() => setShow(!show)}
                    aria-label={show ? t('Login.hide_password', 'Hide password') : t('Login.show_password', 'Show password')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-primary"
                  >
                    <Eye className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <label className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} className="rounded border-[var(--t-border)]" /> Keep me signed in
              </label>

              {error && <p role="alert" className="text-sm text-red-500">{error}</p>}

              <button type="submit" disabled={loading} className="btn-primary inline-flex w-full items-center justify-center gap-2 py-3 text-sm">
                {loading ? <><Spinner className="h-4 w-4 animate-spin" /> Signing in...</> : <>Sign in <ArrowRight className="h-4 w-4" /></>}
              </button>
            </form>

            <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
              New to Studio Lumen?{' '}
              <Link to="/register" className="font-semibold text-primary">{t('Login.create_an_account', t('Login.create_an_account', 'Create an account'))}</Link>
            </p>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
