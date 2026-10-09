import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { Mail, Lock, Eye, ShieldCheck, ArrowRight, LoaderCircle } from 'lucide-react';
import api from '../services/api';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Register() {
  const { t } = useTranslation();
  const [show, setShow] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <Navbar />
      <main id="main-content" className="flex-1 grid lg:grid-cols-2">
        <section
          className="relative hidden lg:flex flex-col justify-between p-12 text-white"
          style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
        >
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.3em] opacity-80">{t('Register.join_aurelia_estates', t('Register.join_aurelia_estates', t('Register.join_aurelia_estates', 'JOIN ClaimFlow')))}</p>
            <h2 className="mt-6 text-4xl font-black leading-tight max-w-sm">{t('Register.start_your_real_estate_journey_today', t('Register.start_your_real_estate_journey_today', t('Register.start_your_real_estate_journey_today', 'Start your real estate journey today')))}</h2>
            <ul className="mt-8 space-y-3 text-sm">
              <li className="flex items-center gap-2"><ShieldCheck className="h-4 w-4" /> Free to join, no card required</li>
              <li className="flex items-center gap-2"><ShieldCheck className="h-4 w-4" /> Set up in under two minutes</li>
              <li className="flex items-center gap-2"><ShieldCheck className="h-4 w-4" /> Cancel or change any time</li>
            </ul>
          </div>
          <p className="text-white/70 text-sm">{t('Register.exceptional_residences_curated_for_the_discerning', t('Register.exceptional_residences_curated_for_the_discerning', t('Register.exceptional_residences_curated_for_the_discerning', 'Exceptional residences, curated for the discerning.')))}</p>
        </section>

        <section className="flex items-center justify-center px-6 py-16">
          <div className="w-full max-w-md" data-reveal>
            <h1 className="text-3xl font-extrabold tracking-tight" style={{ color: 'var(--t-heading)' }}>
              Create your account
            </h1>
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
              Join ClaimFlow in a couple of minutes.
            </p>

            <form onSubmit={async (e) => {
              e.preventDefault();
              setError('');
              if (!name || !email || !password) { setError(t('Register.all_fields_required', 'All fields are required.')); return; }
              if (password.length < 8) { setError(t('Register.password_min_8', 'Password must be at least 8 characters.')); return; }
              setLoading(true);
              try {
                const res = await api.post('/auth/register', { name, email, password });
                if (res.data?.success) {
                  localStorage.setItem('auth_token', res.data.data?.accessToken || '');
                  localStorage.setItem('refresh_token', res.data.data?.refreshToken || '');
                  window.location.href = '/account';
                } else {
                  setError(res.data?.message || t('Register.registration_failed', 'Registration failed. Please try again.'));
                }
              } catch (err) {
                setError(err.response?.data?.message || t('Register.registration_failed', 'Registration failed. Please try again.'));
              } finally {
                setLoading(false);
              }
            }} className="mt-8 space-y-5">
              <div>
                <label htmlFor="name" className="mb-1.5 block text-sm font-medium" style={{ color: 'var(--t-heading)' }}>
                  Full name
                </label>
                <input
                  id="name" name="name" type="text" required autoComplete="name" placeholder="Jane Doe"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full rounded-xl border border-[var(--t-border)] bg-surface px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--t-primary)]"
                />
              </div>
              <div>
                <label htmlFor="email" className="mb-1.5 block text-sm font-medium" style={{ color: 'var(--t-heading)' }}>
                  Email address
                </label>
                <div className="relative">
                  <Mail className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <input
                    id="email" name="email" type="email" required autoComplete="email" placeholder="you@claimflow.test"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full rounded-xl border border-[var(--t-border)] bg-surface py-3 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--t-primary)]"
                  />
                </div>
              </div>
              <div>
                <label htmlFor="password" className="mb-1.5 block text-sm font-medium" style={{ color: 'var(--t-heading)' }}>
                  Password
                </label>
                <div className="relative">
                  <Lock className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <input
                    id="password" name="password" type={show ? 'text' : 'password'} required autoComplete="new-password"
                    placeholder="At least 8 characters"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full rounded-xl border border-[var(--t-border)] bg-surface py-3 pl-10 pr-16 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--t-primary)]"
                  />
                  <button
                    type="button"
                    onClick={() => setShow(!show)}
                    aria-label={show ? t('Register.hide_password', t('Register.hide_password', 'Hide password')) : t('Register.show_password', t('Register.show_password', 'Show password'))}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-primary"
                  >
                    <Eye className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <label className="flex items-start gap-2 text-sm text-slate-500 dark:text-slate-400">
                <input type="checkbox" required className="mt-1 rounded border-[var(--t-border)]" />
                <span>{t('Register.i_agree_to_the_terms_of_service_and_privacy_policy', t('Register.i_agree_to_the_terms_of_service_and_privacy_policy', t('Register.i_agree_to_the_terms_of_service_and_privacy_policy', 'I agree to the Terms of Service and Privacy Policy.')))}</span>
              </label>

              {error && <p role="alert" className="text-sm text-red-500">{error}</p>}

              <button type="submit" disabled={loading} className="btn-primary inline-flex w-full items-center justify-center gap-2 py-3 text-sm">
                {loading ? <><Spinner className="h-4 w-4 animate-spin" /> Creating account...</> : <>Create account <ArrowRight className="h-4 w-4" /></>}
              </button>
            </form>

            <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
              Already have an account?{' '}
              <Link to="/login" className="font-semibold text-primary">{t('Register.sign_in', t('Register.sign_in', t('Register.sign_in', 'Sign in')))}</Link>
            </p>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
