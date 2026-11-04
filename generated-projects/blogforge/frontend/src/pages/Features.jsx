import React from 'react';
import { Link } from 'react-router-dom';
import {
  Zap, Search, Coins, History, ShieldCheck, Gauge, Code2, FileCode2,
  ArrowRight, CheckCircle2, Server, KeyRound,
} from 'lucide-react';

const CORE = [
  {
    icon: Zap,
    title: 'Streaming generation over SSE',
    body: 'The API opens a Server-Sent Events channel and emits a meta frame, then one frame per text delta, then a done frame. The UI renders each chunk as it arrives — no polling, no fake typewriter.',
    points: ['meta → chunk… → done event contract', 'Abort support when you leave the page', 'Graceful error frame with automatic refund'],
  },
  {
    icon: Search,
    title: 'SEO structure, extracted not guessed',
    body: 'The model writes an explicit SEO block; the server parses it into fields. You get a meta title under 70 characters, a meta description, a keyword list and a measured word count.',
    points: ['H1/H2/H3 outline in the body', 'Meta title + description fields', 'Slug generated from the keyword'],
  },
  {
    icon: Coins,
    title: 'Atomic credit accounting',
    body: 'A single UPDATE with a balance guard reserves the credit before generation starts. The same query cannot overdraw an account, even under concurrent requests, and failures refund automatically.',
    points: ['No negative balances', 'Refund on provider failure', 'Granted vs used totals tracked'],
  },
  {
    icon: History,
    title: 'A persistent article library',
    body: 'Every finished article is stored in PostgreSQL under your user id. History is paginated, articles reopen in the generator, and deletion is ownership-checked on the server.',
    points: ['Paginated history endpoint', 'Reopen a draft into the editor', 'Cascade delete with the account'],
  },
  {
    icon: FileCode2,
    title: 'Exports that fit your stack',
    body: 'Markdown for Ghost, Hashnode, Dev.to and static generators. Standalone HTML for WordPress, Webflow or any CMS that accepts custom markup. Copy to clipboard or download a file.',
    points: ['Copy Markdown', 'Download .md', 'Export styled HTML'],
  },
  {
    icon: ShieldCheck,
    title: 'Security on the server, not the client',
    body: 'Passwords are hashed with bcrypt. Sessions are short, signed JWTs. Bodies are schema-validated and HTML-escaped before they reach the database, and SQL is parameterized by the ORM.',
    points: ['JWT bearer auth', 'Input validation + XSS escaping', 'Helmet headers and rate limits'],
  },
];

const PROVIDERS = [
  { name: 'OpenAI', env: 'OPENAI_API_KEY', note: 'GPT models, streamed' },
  { name: 'OpenRouter', env: 'OPENROUTER_API_KEY', note: 'Any routed model' },
  { name: 'DeepSeek', env: 'DEEPSEEK_API_KEY', note: 'Cost-efficient chat models' },
  { name: 'Gemini', env: 'GEMINI_API_KEY', note: 'Google generative API' },
  { name: 'Demo mode', env: '—', note: 'Deterministic, keyless, always available' },
];

export default function Features() {
  return (
    <div className="pb-24">
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 lg:pt-20">
        <div className="max-w-3xl">
          <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold bg-brand-primary/10 text-brand-accent border border-brand-primary/30">
            <Code2 className="w-3.5 h-3.5" /> Product capabilities
          </span>
          <h1 className="mt-6 text-4xl sm:text-5xl font-extrabold tracking-tight text-white">
            Built like infrastructure, priced like a tool
          </h1>
          <p className="mt-5 text-lg text-slate-300 leading-relaxed">
            BlogForge is a full-stack application, not a prompt preset. Streaming transport, metered
            usage, persisted content and real auth are wired end to end — and every piece ships in the
            package you deploy.
          </p>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-14">
        <div className="grid md:grid-cols-2 gap-6">
          {CORE.map(({ icon: Icon, title, body, points }) => (
            <article key={title} className="p-7 rounded-2xl bg-slate-900/60 border border-slate-800">
              <Icon className="w-7 h-7 text-brand-accent mb-4" />
              <h2 className="text-xl font-bold text-white mb-2">{title}</h2>
              <p className="text-sm text-slate-400 leading-relaxed">{body}</p>
              <ul className="mt-4 space-y-2">
                {points.map((p) => (
                  <li key={p} className="flex items-start gap-2 text-xs text-slate-300">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 mt-0.5 shrink-0" /> {p}
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-20">
        <div className="grid lg:grid-cols-2 gap-10 items-start">
          <div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white">The wire protocol</h2>
            <p className="mt-4 text-slate-400 leading-relaxed">
              Generation is a single POST that upgrades to a stream. Any HTTP client can consume it —
              the browser UI uses fetch plus a ReadableStream reader, and the same contract works with
              curl for debugging.
            </p>
            <ul className="mt-6 space-y-3 text-sm text-slate-300">
              <li className="flex items-start gap-3"><Server className="w-4 h-4 text-brand-accent mt-0.5" /> One request, one credit, one stored article.</li>
              <li className="flex items-start gap-3"><KeyRound className="w-4 h-4 text-brand-accent mt-0.5" /> Bearer token required; every query is scoped to the token owner.</li>
              <li className="flex items-start gap-3"><Gauge className="w-4 h-4 text-brand-accent mt-0.5" /> Provider timeouts return an error frame, not a broken stream.</li>
            </ul>
          </div>
          <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5 font-mono text-xs leading-relaxed text-slate-300 overflow-x-auto">
            <p className="text-slate-500">POST /api/v1/blog/generate</p>
            <p className="text-slate-500">Authorization: Bearer &lt;jwt&gt;</p>
            <p className="mt-4 text-slate-500">{"{"} "keyword": "ai seo tools", "tone": "professional", "length": "short" {"}"}</p>
            <pre className="mt-4 whitespace-pre-wrap text-emerald-300">{`event: meta
data: {"balance":49,"demo":true}

event: chunk
data: "# ai seo tools\\n\\n## Why it matters…"

event: done
data: {"articleId":"…","creditsUsed":1,"balance":49}`}</pre>
          </div>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-20">
        <div className="rounded-3xl border border-slate-800 bg-slate-900/40 overflow-hidden">
          <div className="p-7 sm:p-9 border-b border-slate-800">
            <h2 className="text-2xl font-extrabold text-white">Bring your own provider</h2>
            <p className="mt-3 text-sm text-slate-400 max-w-2xl">
              One client abstraction, five backends. Set a key and the provider switches automatically;
              with no key the demo engine keeps every screen functional.
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wider text-slate-500 border-b border-slate-800">
                  <th className="px-7 py-3 font-semibold">Backend</th>
                  <th className="px-7 py-3 font-semibold">Environment variable</th>
                  <th className="px-7 py-3 font-semibold">Notes</th>
                </tr>
              </thead>
              <tbody>
                {PROVIDERS.map(({ name, env, note }) => (
                  <tr key={name} className="border-b border-slate-800/60 last:border-0">
                    <td className="px-7 py-4 font-semibold text-white">{name}</td>
                    <td className="px-7 py-4 font-mono text-xs text-brand-accent">{env}</td>
                    <td className="px-7 py-4 text-slate-400">{note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 mt-20">
        <div className="rounded-3xl border border-brand-primary/30 bg-gradient-to-br from-brand-primary/15 via-slate-900 to-slate-950 p-10 text-center">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white">See it with your own keyword</h2>
          <p className="mt-3 text-slate-300">Create an account and run the full stream in under a minute.</p>
          <Link
            to="/register"
            className="mt-7 inline-flex items-center gap-2 px-7 py-3.5 rounded-full font-bold text-white bg-gradient-to-r from-brand-primary to-cyan-500 hover:opacity-95 transition-all duration-200"
          >
            Start free <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>
    </div>
  );
}
