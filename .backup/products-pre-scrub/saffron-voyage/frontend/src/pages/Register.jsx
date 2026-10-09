import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, Lock, Eye, ShieldCheck, ArrowRight } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Register() {
  const [show, setShow] = useState(false);

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <Navbar />
      <main className="flex-1 grid lg:grid-cols-2">
        <section
          className="relative hidden lg:flex flex-col justify-between p-12 text-white"
          style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
        >
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.3em] opacity-80">JOIN Saffron Voyage</p>
            <h2 className="mt-6 text-4xl font-black leading-tight max-w-sm">Start your hospitality journey today</h2>
            <ul className="mt-8 space-y-3 text-sm">
              <li className="flex items-center gap-2"><ShieldCheck className="h-4 w-4" /> Free to join, no card required</li>
              <li className="flex items-center gap-2"><ShieldCheck className="h-4 w-4" /> Set up in under two minutes</li>
              <li className="flex items-center gap-2"><ShieldCheck className="h-4 w-4" /> Cancel or change any time</li>
            </ul>
          </div>
          <p className="text-white/70 text-sm">Journeys woven from local story.</p>
        </section>

        <section className="flex items-center justify-center px-6 py-16">
          <div className="w-full max-w-md" data-reveal>
            <h1 className="text-3xl font-extrabold tracking-tight" style={{ color: 'var(--t-heading)' }}>
              Create your account
            </h1>
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
              Join Saffron Voyage in a couple of minutes.
            </p>

            <form onSubmit={(e) => e.preventDefault()} className="mt-8 space-y-5">
              <div>
                <label htmlFor="name" className="mb-1.5 block text-sm font-medium" style={{ color: 'var(--t-heading)' }}>
                  Full name
                </label>
                <input
                  id="name" name="name" type="text" required autoComplete="name" placeholder="Jane Doe"
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
                    id="email" name="email" type="email" required autoComplete="email" placeholder="you@example.com"
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
                    className="w-full rounded-xl border border-[var(--t-border)] bg-surface py-3 pl-10 pr-16 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--t-primary)]"
                  />
                  <button
                    type="button"
                    onClick={() => setShow(!show)}
                    aria-label={show ? t('Register.hide_password', 'Hide password') : t('Register.show_password', 'Show password')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-primary"
                  >
                    <Eye className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <label className="flex items-start gap-2 text-sm text-slate-500 dark:text-slate-400">
                <input type="checkbox" required className="mt-1 rounded border-[var(--t-border)]" />
                <span>{t('Register.i_agree_to_the_terms_of_service_and_privacy_policy', t('Register.i_agree_to_the_terms_of_service_and_privacy_policy', 'I agree to the Terms of Service and Privacy Policy.'))}</span>
              </label>

              <button type="submit" className="btn-primary inline-flex w-full items-center justify-center gap-2 py-3 text-sm">
                Create account <ArrowRight className="h-4 w-4" />
              </button>
            </form>

            <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
              Already have an account?{' '}
              <Link to="/login" className="font-semibold text-primary">{t('Register.sign_in', t('Register.sign_in', 'Sign in'))}</Link>
            </p>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
