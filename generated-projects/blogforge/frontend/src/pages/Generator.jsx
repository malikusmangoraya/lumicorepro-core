import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { marked } from 'marked';
import {
  Sparkles, Wand2, Loader2, Target, Users,
  MessageSquareText, AlignLeft, ChevronDown, RotateCcw,
} from 'lucide-react';
import { useToast } from '../components/common/Toast.jsx';
import ExportButtons from '../components/generator/ExportButtons.jsx';
import ArticleSkeleton from '../components/generator/ArticleSkeleton.jsx';
import { sanitizeHtml } from '../components/generator/sanitize.js';
import { getAuthToken } from '../auth.js';

const API = import.meta.env.VITE_API_URL || 'http://localhost:5000/api/v1';
const TONES = ['Professional', 'Friendly', 'Casual', 'Humorous', 'Informative'];
const LENGTHS = [
  { key: 'short', label: 'Short', hint: 'â‰ˆ600 words' },
  { key: 'medium', label: 'Medium', hint: 'â‰ˆ1200 words' },
  { key: 'long', label: 'Long', hint: 'â‰ˆ2200 words' },
];

marked.setOptions({ gfm: true, breaks: true });

export default function Generator() {
  const { toast } = useToast();
  const { setBalance } = useOutletContext() || {};
  const [keyword, setKeyword] = useState('');
  const [audience, setAudience] = useState('');
  const [tone, setTone] = useState('professional');
  const [length, setLength] = useState('medium');
  const [busy, setBusy] = useState(false);
  const [streamed, setStreamed] = useState('');
  const [meta, setMeta] = useState(null); // { demo }
  const [result, setResult] = useState(null); // done payload
  const [error, setError] = useState('');
  const outputRef = useRef(null);
  const abortRef = useRef(null);

  useEffect(() => {
    if (outputRef.current && streamed) outputRef.current.scrollTop = outputRef.current.scrollHeight;
  }, [streamed]);

  // Restore an article opened from History (stashed by restore())
  useEffect(() => {
    try {
      const raw = sessionStorage.getItem('bf-restore');
      if (!raw) return;
      const a = JSON.parse(raw);
      setKeyword(a.keyword || orString(a.title));
      setAudience(a.audience || '');
      setTone((a.tone || 'professional').toLowerCase());
      setLength(a.length || 'medium');
      setStreamed(a.content || '');
      setResult({
        id: a.id, title: a.title, slug: a.slug, wordCount: a.wordCount,
        demo: a.demo, metaTitle: a.metaTitle, metaDescription: a.metaDescription,
        keywords: a.keywords,
      });
    } catch { /* ignore malformed stash */ } finally {
      sessionStorage.removeItem('bf-restore');
    }
  }, []);

  const reset = () => { setStreamed(''); setMeta(null); setResult(null); setError(''); };

  const orString = (v) => (typeof v === 'string' ? v : '');

  const generate = useCallback(async (overrides = {}) => {
    reset();
    setBusy(true);
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    try {
      const token = getAuthToken() || '';
      const res = await fetch(`${API}/blog/generate`, {
        method: 'POST',
        signal: ctrl.signal,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
          'X-Force-Demo': overrides.forceDemo ? '1' : undefined,
        },
        body: JSON.stringify({
          keyword: overrides.keyword ?? keyword,
          audience: overrides.audience ?? audience,
          tone: tone.toLowerCase(),
          length,
        }),
      });
      if (!res.ok || !res.body) {
        const j = await res.json().catch(() => ({}));
        throw new Error(j.message || `HTTP ${res.status}`);
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = '';
      let text = '';
      let done = false;
      while (!done) {
        const { value, done: rd } = await reader.read();
        if (rd) break;
        buf += decoder.decode(value, { stream: true });
        const frames = buf.split('\n\n');
        buf = frames.pop() || '';
        for (const frame of frames) {
          const evLine = frame.split('\n').find((l) => l.startsWith('event: '));
          const dataLine = frame.split('\n').find((l) => l.startsWith('data: '));
          if (!dataLine) continue;
          const event = evLine?.slice(7).trim();
          const payload = JSON.parse(dataLine.slice(6) || '{}');
          if (event === 'meta') setMeta(payload);
          if (event === 'chunk') { text += payload; setStreamed(text); }
          if (event === 'done') {
            done = true;
            setResult(payload);
            if (typeof payload.balance === 'number') setBalance?.(payload.balance);
          }
          if (event === 'error') throw new Error(payload.message || 'Generation failed');
        }
      }
      if (done) toast('Article generated â€” 1 credit used');
    } catch (e) {
      setError(e.message || 'Generation failed');
      toast(e.message || 'Generation failed', 'error');
    } finally {
      setBusy(false);
      abortRef.current = null;
    }
  }, [keyword, audience, tone, length, toast, setBalance]);

  return (
    <div className="grid lg:grid-cols-[380px_1fr] xl:grid-cols-[420px_1fr] min-h-screen">
      {/* â”€â”€ Left panel: input controls â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <section className="p-6 lg:p-8 border-b lg:border-b-0 lg:border-r border-slate-800 bg-slate-900/40 space-y-6" aria-labelledby="gen-heading">
        <div>
          <h1 id="gen-heading" className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Wand2 className="w-6 h-6 text-indigo-400" /> New Article
          </h1>
          <p className="text-sm text-slate-400 mt-1">One keyword in, a full SEO-optimized post out.</p>
        </div>

        <div className="space-y-1.5">
          <label htmlFor="bf-keyword" className="text-xs font-semibold uppercase tracking-wide text-slate-400">Target keyword *</label>
          <input
            id="bf-keyword"
            data-testid="gen-keyword"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="Best JavaScript Frameworks 2026"
            maxLength={160}
            disabled={busy}
            className="w-full px-4 py-3 rounded-xl bg-slate-800/70 border border-slate-700 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/30 outline-none text-sm placeholder:text-slate-600 transition-all duration-200"
          />
        </div>

        <div className="space-y-1.5">
          <label htmlFor="bf-audience" className="text-xs font-semibold uppercase tracking-wide text-slate-400 flex items-center gap-1.5"><Users className="w-3.5 h-3.5" /> Target audience</label>
          <input
            id="bf-audience"
            value={audience}
            onChange={(e) => setAudience(e.target.value)}
            placeholder="e.g. startup founders, students"
            maxLength={160}
            disabled={busy}
            className="w-full px-4 py-3 rounded-xl bg-slate-800/70 border border-slate-700 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/30 outline-none text-sm placeholder:text-slate-600 transition-all duration-200"
          />
        </div>

        <div className="space-y-1.5">
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-400 flex items-center gap-1.5"><MessageSquareText className="w-3.5 h-3.5" /> Tone</span>
          <div className="relative">
            <select
              aria-label="Tone"
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              disabled={busy}
              className="w-full appearance-none px-4 py-3 rounded-xl bg-slate-800/70 border border-slate-700 focus:border-indigo-400 outline-none text-sm transition-all duration-200"
            >
              {TONES.map((t) => <option key={t} value={t.toLowerCase()}>{t}</option>)}
            </select>
            <ChevronDown className="w-4 h-4 text-slate-500 absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>

        <div className="space-y-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-400 flex items-center gap-1.5"><AlignLeft className="w-3.5 h-3.5" /> Article length</span>
          <div className="grid grid-cols-3 gap-2" role="radiogroup" aria-label="Article length">
            {LENGTHS.map((l) => (
              <button
                key={l.key}
                type="button"
                role="radio"
                aria-checked={length === l.key}
                onClick={() => setLength(l.key)}
                disabled={busy}
                className={`px-3 py-3 rounded-xl text-center transition-all duration-200 border ${
                  length === l.key
                    ? 'bg-gradient-to-br from-indigo-500/25 to-fuchsia-500/10 border-indigo-400/50 text-white'
                    : 'bg-slate-800/50 border-slate-700 text-slate-400 hover:text-white hover:border-slate-600'
                }`}
              >
                <span className="block text-sm font-semibold">{l.label}</span>
                <span className="block text-[10px] text-slate-500 mt-0.5">{l.hint}</span>
              </button>
            ))}
          </div>
        </div>

        <button
          type="button"
          data-testid="gen-submit"
          onClick={() => generate()}
          disabled={busy || keyword.trim().length < 3}
          className="btn-glow w-full flex items-center justify-center gap-2 px-6 py-4 rounded-xl font-bold text-white bg-gradient-to-r from-indigo-500 to-fuchsia-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200"
        >
          {busy ? <Loader2 className="w-5 h-5 animate-spin" /> : <Sparkles className="w-5 h-5" />}
          {busy ? 'Writing your articleâ€¦' : 'Generate Article'}
        </button>

        <p className="text-xs text-slate-500 flex items-center gap-1.5">
          <Target className="w-3.5 h-3.5" /> Costs 1 credit per generation Â· credits refund on failure
        </p>
      </section>

      {/* â”€â”€ Right panel: live output â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <section ref={outputRef} className="p-6 lg:p-10 flex flex-col min-w-0 lg:max-h-screen lg:overflow-y-auto" aria-label="Article output">
        {busy && !streamed && (
          <>
            <div className="flex items-center gap-2 text-indigo-300 text-sm mb-6 animate-pulse-soft">
              <Sparkles className="w-4 h-4" /> BlogForge is researching your keywordâ€¦
            </div>
            <ArticleSkeleton />
          </>
        )}

        {!busy && !streamed && !result && !error && (
          <div className="flex-1 grid place-items-center text-center py-24">
            <div className="max-w-md space-y-3">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-fuchsia-500/10 border border-indigo-500/30 grid place-items-center mx-auto">
                <Wand2 className="w-8 h-8 text-indigo-400" />
              </div>
              <h2 className="text-xl font-bold">Your article appears here</h2>
              <p className="text-sm text-slate-400">Enter a keyword on the left and hit generate â€” you'll watch the article write itself, complete with H2/H3 structure and SEO metadata.</p>
            </div>
          </div>
        )}

        {error && (
          <div role="alert" data-testid="gen-error" className="mx-auto max-w-xl my-16 text-center space-y-4">
            <div className="px-6 py-5 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-200 text-sm">{error}</div>
            <button type="button" onClick={() => generate()} className="inline-flex items-center gap-2 text-sm text-indigo-300 hover:text-white transition-all duration-200">
              <RotateCcw className="w-4 h-4" /> Try again (credits are refunded automatically)
            </button>
          </div>
        )}

        {(streamed || result) && (
          <article className="max-w-3xl w-full mx-auto" data-testid="gen-article">
            {result && (
              <header className="mb-8 pb-6 border-b border-slate-800 space-y-4 animate-fade-in">
                <h1 className="text-3xl font-extrabold tracking-tight text-white">{result.title}</h1>
                <dl className="grid sm:grid-cols-2 gap-3 text-xs">
                  {result.metaTitle && (
                    <div className="px-3 py-2 rounded-lg bg-slate-800/50 border border-slate-700/50">
                      <dt className="text-slate-400">SEO title</dt>
                      <dd className="text-slate-200 mt-0.5">{result.metaTitle}</dd>
                    </div>
                  )}
                  {result.metaDescription && (
                    <div className="px-3 py-2 rounded-lg bg-slate-800/50 border border-slate-700/50 sm:col-span-2">
                      <dt className="text-slate-400">Meta description</dt>
                      <dd className="text-slate-200 mt-0.5">{result.metaDescription}</dd>
                    </div>
                  )}
                  <div className="px-3 py-2 rounded-lg bg-slate-800/50 border border-slate-700/50">
                    <dt className="text-slate-400">Slug</dt>
                    <dd className="text-slate-200 mt-0.5 font-mono text-[11px]">/{result.slug}</dd>
                  </div>
                  <div className="px-3 py-2 rounded-lg bg-slate-800/50 border border-slate-700/50">
                    <dt className="text-slate-400">Stats</dt>
                    <dd className="text-slate-200 mt-0.5">{result.wordCount} words{result.demo ? ' Â· demo mode' : ''}</dd>
                  </div>
                </dl>
                <ExportButtons markdown={streamed} title={result.title} onToast={toast} />
              </header>
            )}
            <div className="prose-bf animate-fade-in" data-testid="gen-preview" dangerouslySetInnerHTML={{ __html: sanitizeHtml(marked(streamed || '')) }} />
          </article>
        )}
      </section>
    </div>
  );
}
