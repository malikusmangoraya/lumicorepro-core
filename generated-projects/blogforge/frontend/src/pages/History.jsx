import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, Trash2, RotateCcw } from 'lucide-react';
import { useToast } from '../components/common/Toast.jsx';
import { useLocale } from '../i18n.js';

const API = import.meta.env.VITE_API_URL || 'http://localhost:5000/api/v1';

export default function History() {
  const { toast } = useToast();
  const navigate = useNavigate();
  const locale = useLocale();
  const [items, setItems] = useState(null);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setError('');
    try {
      const res = await fetch(`${API}/blog/history?limit=50`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token') || ''}` },
      });
      const json = await res.json();
      if (!res.ok || !json.success) throw new Error(json.message || `HTTP ${res.status}`);
      setItems(json.data || []);
    } catch (e) {
      setError(e.message || 'Failed to load history');
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const restore = async (id) => {
    try {
      const res = await fetch(`${API}/blog/articles/${id}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token') || ''}` },
      });
      const json = await res.json();
      if (!res.ok || !json.success) throw new Error(json.message || 'Could not open article');
      sessionStorage.setItem('bf-restore', JSON.stringify(json.data));
      navigate('/generate');
      toast('Article restored — open the editor');
    } catch (e) {
      toast(e.message, 'error');
    }
  };

  const remove = async (id) => {
    try {
      const res = await fetch(`${API}/blog/articles/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${localStorage.getItem('token') || ''}` },
      });
      if (!res.ok) throw new Error('Delete failed');
      setItems((list) => (Array.isArray(list) ? list.filter((article) => article.id !== id) : list));
      toast('Article deleted');
    } catch (e) {
      toast(e.message, 'error');
    }
  };

  const formatArticleDate = (date) => new Intl.DateTimeFormat(
    locale === 'ur' ? 'ur-PK' : 'en-US',
    { dateStyle: 'medium' },
  ).format(new Date(date));

  return (
    <div className="p-6 lg:p-10 max-w-4xl min-h-screen" data-testid="history-page">
      <div className="flex items-center gap-3 mb-8">
        <BookOpen className="w-7 h-7 text-indigo-400" />
        <h1 className="text-2xl font-bold tracking-tight">Article History</h1>
        <span className="text-sm text-slate-500 ml-auto">{items ? `${items.length} saved` : ''}</span>
      </div>

      {error && (
        <div role="alert" className="px-5 py-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-200 text-sm flex items-center justify-between">
          {error}
          <button type="button" onClick={load} className="inline-flex items-center gap-1 text-xs hover:text-white"><RotateCcw className="w-3.5 h-3.5" /> Retry</button>
        </div>
      )}

      {items === null && !error && (
        <div className="space-y-3" aria-hidden="true">
          {[0, 1, 2].map((index) => <div key={index} className="h-20 rounded-2xl bg-slate-800/60 border border-slate-700/50 animate-shimmer" />)}
        </div>
      )}

      {items?.length === 0 && !error && (
        <div className="text-center py-24 space-y-3" data-testid="history-empty">
          <p className="text-slate-400">No articles yet.</p>
          <button type="button" onClick={() => navigate('/generate')} className="text-sm font-semibold text-indigo-300 hover:text-white transition-all duration-200">Write your first article →</button>
        </div>
      )}
      {items?.length > 0 && (
        <ul className="space-y-3">
          {items.map((article) => (
            <li key={article.id} className="group flex items-start gap-4 p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-indigo-500/40 transition-all duration-200">
              <div className="min-w-0 flex-1">
                <p className="font-semibold text-white truncate">{article.title}</p>
                <p className="text-xs text-slate-500 mt-1">
                  {article.keyword} · {article.tone} · {article.length} · {article.wordCount} words · {formatArticleDate(article.createdAt)}
                  {article.demo && <span className="ml-2 px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30">demo</span>}
                </p>
              </div>
              <button type="button" onClick={() => restore(article.id)} aria-label={`Open ${article.title}`} className="p-2 rounded-lg text-slate-400 hover:text-indigo-300 hover:bg-slate-800 transition-all duration-200">
                <BookOpen className="w-4 h-4" />
              </button>
              <button type="button" onClick={() => remove(article.id)} aria-label={`Delete ${article.title}`} className="p-2 rounded-lg text-slate-400 hover:text-red-300 hover:bg-slate-800 transition-all duration-200">
                <Trash2 className="w-4 h-4" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
