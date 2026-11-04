import React, { useCallback, useEffect, useState } from 'react';
import { Coins, Plus, BarChart3, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { useOutletContext } from 'react-router-dom';
import { useToast } from '../components/common/Toast.jsx';
import { formatNumber, translate, useLocale } from '../i18n.js';

const API = import.meta.env.VITE_API_URL || 'http://localhost:5000/api/v1';
const PACKS = [50, 150, 500];

export default function Credits() {
  const { toast } = useToast();
  const outlet = useOutletContext() || {};
  const locale = useLocale();
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const res = await fetch(`${API}/blog/credits`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token') || ''}` },
      });
      const json = await res.json();
      if (!res.ok || !json.success) throw new Error(json.message || 'Failed to load credits');
      setData(json.data);
    } catch (e) {
      setError(e.message);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const topup = async (amount) => {
    setBusy(true);
    try {
      const res = await fetch(`${API}/blog/credits/topup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('token') || ''}` },
        body: JSON.stringify({ amount }),
      });
      const json = await res.json();
      if (!res.ok || !json.success) throw new Error(json.message || 'Top-up failed');
      toast(`+${formatNumber(amount, locale)} evaluation credits added`);
      await load();
      outlet.setBalance?.(json.data.balance);
    } catch (e) {
      toast(e.message, 'error');
    } finally {
      setBusy(false);
    }
  };

  const usedPct = data && data.totalGranted > 0 ? Math.round((data.totalUsed / data.totalGranted) * 100) : 0;

  return (
    <div className="p-6 lg:p-10 max-w-3xl min-h-screen" data-testid="credits-page">
      <div className="flex items-center gap-3 mb-8">
        <Coins className="w-7 h-7 text-amber-300" />
        <h1 className="text-2xl font-bold tracking-tight">Evaluation Credits</h1>
      </div>

      <p role="status" className="mb-6 rounded-xl border border-amber-400/30 bg-amber-400/10 p-4 text-sm text-amber-100">
        {translate(locale, 'evaluationPricing')}
      </p>

      {error && <div role="alert" className="px-5 py-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-200 text-sm">{error}</div>}

      {data && (
        <>
          <div className="p-8 rounded-3xl bg-gradient-to-br from-indigo-500/15 via-slate-900/40 to-fuchsia-500/10 border border-indigo-500/25 mb-8">
            <p className="text-sm text-slate-400">Available evaluation balance</p>
            <p className="text-6xl font-extrabold tabular-nums bg-gradient-to-r from-indigo-400 to-fuchsia-400 bg-clip-text text-transparent my-2" data-testid="credits-balance">{formatNumber(data.balance, locale)}</p>
            <div className="mt-4" aria-hidden="true">
              <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                <div className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-fuchsia-500 transition-all duration-500" style={{ width: `${Math.min(usedPct, 100)}%` }} />
              </div>
            </div>
            <div className="flex gap-6 mt-3 text-xs text-slate-400">
              <span className="inline-flex items-center gap-1"><ArrowUpRight className="w-3.5 h-3.5 text-emerald-400" /> granted {formatNumber(data.totalGranted, locale)}</span>
              <span className="inline-flex items-center gap-1"><ArrowDownRight className="w-3.5 h-3.5 text-indigo-300" /> used {formatNumber(data.totalUsed, locale)}</span>
            </div>
          </div>

          <section aria-labelledby="topup-heading">
            <h2 id="topup-heading" className="text-sm font-semibold uppercase tracking-wide text-slate-400 flex items-center gap-2 mb-3"><Plus className="w-4 h-4" /> Evaluation top-up (no payment)</h2>
            <div className="grid grid-cols-3 gap-3">
              {PACKS.map((amount) => (
                <button
                  key={amount}
                  type="button"
                  onClick={() => topup(amount)}
                  disabled={busy}
                  className="btn-glow px-4 py-5 rounded-2xl bg-slate-900/70 border border-slate-800 hover:border-indigo-400/60 transition-all duration-200 disabled:opacity-50"
                >
                  <span className="block text-2xl font-bold text-white">{formatNumber(amount, locale)}</span>
                  <span className="block text-xs text-slate-400 mt-1">evaluation credits</span>
                </button>
              ))}
            </div>
            <p className="text-xs text-slate-500 mt-3 flex items-center gap-1.5"><BarChart3 className="w-3.5 h-3.5" /> 1 credit = 1 article generation. Failed generations are refunded automatically.</p>
          </section>
        </>
      )}
    </div>
  );
}
