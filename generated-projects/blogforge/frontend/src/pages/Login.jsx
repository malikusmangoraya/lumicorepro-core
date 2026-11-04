import React, { useState } from 'react';
import { Link, useNavigate, Navigate, useSearchParams } from 'react-router-dom';
import { saveAuthSession } from '../auth.js';
import { LogIn, Loader2, AlertCircle } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:5000/api/v1';

export default function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [signedIn] = useState(() => Boolean(localStorage.getItem('token')));

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      const res = await fetch(`${API}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const json = await res.json();
      if (!res.ok || !json.token) throw new Error(json.message || 'Invalid credentials');
      saveAuthSession(json.token, json.user || { email });
      const next = searchParams.get('next');
      navigate(next?.startsWith('/generate') ? next : '/generate', { replace: true });
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setBusy(false);
    }
  };

  if (signedIn) return <Navigate to="/generate" replace />;
  return (
    <div className="max-w-md mx-auto px-6 py-24">
      <h1 className="text-3xl font-bold text-white text-center mb-8">Sign in to BlogForge</h1>
      <form onSubmit={submit} className="p-8 rounded-3xl bg-slate-900 border border-slate-800 space-y-4">
        {error && (
          <div role="alert" className="flex items-start gap-2 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-200 text-sm">
            <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" /> {error}
          </div>
        )}
        <div className="space-y-1.5">
          <label htmlFor="login-email" className="text-xs font-semibold text-slate-400">Email</label>
          <input
            id="login-email"
            data-testid="login-email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/30 outline-none transition-all duration-200"
          />
        </div>
        <div className="space-y-1.5">
          <label htmlFor="login-password" className="text-xs font-semibold text-slate-400">Password</label>
          <input
            id="login-password"
            data-testid="login-password"
            type="password"
            autoComplete="current-password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/30 outline-none transition-all duration-200"
          />
        </div>
        <button
          type="submit"
          data-testid="login-submit"
          disabled={busy}
          className="btn-glow w-full flex items-center justify-center gap-2 py-3.5 rounded-xl bg-gradient-to-r from-indigo-500 to-fuchsia-500 text-white font-bold disabled:opacity-50 transition-all duration-200"
        >
          {busy ? <Loader2 className="w-5 h-5 animate-spin" /> : <LogIn className="w-5 h-5" />} Sign In
        </button>
        <p className="text-center text-sm text-slate-400">
          No account? <Link to="/register" className="text-indigo-300 hover:text-white">Create one</Link> — 50 free credits included.
        </p>
      </form>
    </div>
  );
}
