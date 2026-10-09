import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Download, Trash2 } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Account() {
  const { t } = useTranslation();
  const [password, setPassword] = useState('');
  const [msg, setMsg] = useState('');

  const exportData = async () => {
    try {
      const r = await fetch('/api/auth/account/export', { credentials: 'include' });
      if (!r.ok) throw new Error('unauthorised');
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = 'account-export.json'; a.click();
      URL.revokeObjectURL(url);
    } catch { setMsg(t('Account.exportFailed', 'Sign in to export your data.')); }
  };

  const deleteAccount = async () => {
    if (!window.confirm(t('Account.confirmDelete', 'Permanently delete your account?'))) return;
    try {
      const r = await fetch('/api/auth/account', {
        method: 'DELETE', credentials: 'include',
        headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ password }),
      });
      const j = await r.json();
      setMsg(r.ok ? t('Account.deleted', 'Account deleted.') : (j.error || t('Account.deleteFailed', 'Could not delete.')));
    } catch { setMsg(t('Account.deleteFailed', 'Could not delete.')); }
  };

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <Navbar />
      <main id="main-content" className="flex-1 py-12 px-4">
        <div className="max-w-3xl mx-auto">
          <p className="section-eyebrow">{t('Account.eyebrow', 'Privacy')}</p>
          <h1 className="section-heading mt-1">{t('Account.title', 'Your data')}</h1>
          <div className="card-panel p-7 mt-8 grid gap-6">
            <button onClick={exportData} className="btn-outline inline-flex items-center justify-center gap-2 py-3">
              <Download className="h-4 w-4" /> {t('Account.export', 'Export my data')}
            </button>
            <div>
              <label htmlFor="account-password" className="block text-sm font-medium mb-1" style={{ color: 'var(--t-heading)' }}>
                {t('Account.password', 'Current password')}
              </label>
              <input id="account-password" type="password" value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-[var(--t-border)] bg-surface px-3 py-2" />
            </div>
            <button onClick={deleteAccount} className="btn-danger inline-flex items-center justify-center gap-2 py-3">
              <Trash2 className="h-4 w-4" /> {t('Account.delete', 'Delete my account')}
            </button>
            {msg && <p className="text-sm text-slate-500">{msg}</p>}
            <p className="text-xs text-slate-400">{t('Account.note', 'Deleting removes the account and its stored data. This cannot be undone.')}</p>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
