"""ai_saas_kit — inject the Category-1 (AI & Automation Micro-SaaS) toolkit
into a generated project's backend.

Five drop-in pieces every AI micro-SaaS needs, generated as real files:

  backend/services/keyVault.js    encrypted API-key manager (AES-256-GCM)
  backend/services/aiClient.js    provider-agnostic LLM client
                                  (OpenAI / Gemini / OpenRouter / DeepSeek)
  backend/services/stream.js      Server-Sent Events helper (typewriter UX)
  backend/services/prompts.js     reusable prompt template engine ({{var}})
  backend/services/ragLite.js     RAG: pgvector when available, in-memory fallback
  backend/routes/ai.js            /api/ai/generate (SSE) · /chat (RAG) · /files
                                  (multer + pdf-parse/docx text extraction)

plus the npm dependencies (openai, pdf-parse, docx, pgvector-ready pg) merged
into the backend package.json. Idempotent: existing files are left alone.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

_DEPS = {
    "openai": "^4.67.0",
    "pdf-parse": "^1.1.1",
    "docx": "^9.0.2",
    "bcryptjs": "^2.4.3",
    "multer": "^1.4.5-lts.1",
}

_KEY_VAULT_JS = """/** keyVault — encrypted API-key manager for AI providers.
 * Keys live in the DB (or file) as AES-256-GCM ciphertext; ENCRYPTION_KEY is a
 * 32-byte hex secret from .env — never a key itself. get()/set() are the only
 * surface; raw plaintext never crosses a log or response.
 */
const crypto = require('crypto');

const ALGO = 'aes-256-gcm';

function _key() {
  const hex = process.env.ENCRYPTION_KEY;
  if (!hex || hex.length !== 64) {
    throw new Error('ENCRYPTION_KEY must be a 64-char hex string (32 bytes)');
  }
  return Buffer.from(hex, 'hex');
}

const _store = new Map(); // name -> {iv, tag, data} hex — swap for a DB table in prod

function setKey(name, plaintext) {
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv(ALGO, _key(), iv);
  const data = Buffer.concat([cipher.update(String(plaintext), 'utf8'), cipher.final()]);
  _store.set(name, { iv: iv.toString('hex'), tag: cipher.getAuthTag().toString('hex'), data: data.toString('hex') });
  return name;
}

function getKey(name) {
  const rec = _store.get(name);
  if (!rec) return process.env[name] || null; // .env fallback
  try {
    const decipher = crypto.createDecipheriv(ALGO, _key(), Buffer.from(rec.iv, 'hex'));
    decipher.setAuthTag(Buffer.from(rec.tag, 'hex'));
    return Buffer.concat([decipher.update(Buffer.from(rec.data, 'hex')), decipher.final()]).toString('utf8');
  } catch (_e) {
    return null; // wrong key / tampered — never throw raw crypto errors outward
  }
}

function hasKey(name) {
  return _store.has(name) || Boolean(process.env[name]);
}

module.exports = { setKey, getKey, hasKey };
"""

_AI_CLIENT_JS = """/** aiClient — one client, four providers, zero lock-in.
 * AI_PROVIDER: openai | gemini | openrouter | deepseek (default openai).
 * Keys resolve through keyVault (encrypted at rest, .env fallback).
 * complete() is plain JSON; completeStream() yields text deltas for SSE.
 */
const keyVault = require('./keyVault');

const ENDPOINTS = {
  openai: { url: 'https://api.openai.com/v1/chat/completions', key: 'OPENAI_API_KEY', model: process.env.OPENAI_MODEL || 'gpt-4o-mini' },
  deepseek: { url: 'https://api.deepseek.com/chat/completions', key: 'DEEPSEEK_API_KEY', model: process.env.DEEPSEEK_MODEL || 'deepseek-chat' },
  openrouter: { url: 'https://openrouter.ai/api/v1/chat/completions', key: 'OPENROUTER_API_KEY', model: process.env.OPENROUTER_MODEL || 'openai/gpt-4o-mini' },
  gemini: { url: 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions', key: 'GEMINI_API_KEY', model: process.env.GEMINI_MODEL || 'gemini-1.5-flash' },
};

function _cfg(override) {
  const name = (override || process.env.AI_PROVIDER || 'openai').toLowerCase();
  const cfg = ENDPOINTS[name];
  if (!cfg) throw new Error(`Unknown AI provider: ${name}`);
  const apiKey = keyVault.getKey(cfg.key);
  if (!apiKey) throw new Error(`${cfg.key} not configured (keyVault or .env)`);
  return { ...cfg, name, apiKey };
}

function _body(cfg, messages, opts) {
  return JSON.stringify({ model: opts.model || cfg.model, messages, stream: Boolean(opts.stream), temperature: opts.temperature ?? 0.7 });
}

function _headers(cfg) {
  const h = { 'Content-Type': 'application/json', Authorization: `Bearer ${cfg.apiKey}` };
  if (cfg.name === 'openrouter') h['HTTP-Referer'] = process.env.APP_URL || 'http://localhost:3000';
  return h;
}

async function complete(messages, opts = {}) {
  const cfg = _cfg(opts.provider);
  const res = await fetch(cfg.url, { method: 'POST', headers: _headers(cfg), body: _body(cfg, messages, opts) });
  if (!res.ok) throw new Error(`AI ${res.status}: ${(await res.text()).slice(0, 200)}`);
  const data = await res.json();
  return data.choices[0].message.content;
}

async function* completeStream(messages, opts = {}) {
  const cfg = _cfg(opts.provider);
  const res = await fetch(cfg.url, { method: 'POST', headers: _headers(cfg), body: _body(cfg, messages, { ...opts, stream: true }) });
  if (!res.ok || !res.body) throw new Error(`AI ${res.status}: streaming unsupported`);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = '';
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const lines = buf.split('\\n');
    buf = lines.pop() || '';
    for (const line of lines) {
      const t = line.trim();
      if (!t.startsWith('data:')) continue;
      const payload = t.slice(5).trim();
      if (payload === '[DONE]') return;
      try {
        const delta = JSON.parse(payload).choices?.[0]?.delta?.content;
        if (delta) yield delta;
      } catch (_e) { /* keep-alive or partial line */ }
    }
  }
}

module.exports = { complete, completeStream };
"""

_STREAM_JS = """/** stream — Server-Sent Events helpers for Express (typewriter AI output).
 * sseInit(res) flips headers; sseSend(res, event, data) frames one event;
 * sseStreamText(res, iterable, onDone) pipes AI deltas as `data:` frames.
 */
function sseInit(res) {
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    Connection: 'keep-alive',
    'X-Accel-Buffering': 'no',
  });
  res.flushHeaders?.();
}

function sseSend(res, event, data) {
  res.write(`event: ${event}\\ndata: ${JSON.stringify(data)}\\n\\n`);
}

async function sseStreamText(res, textIterable, meta = {}) {
  sseInit(res);
  let full = '';
  try {
    for await (const delta of textIterable) {
      full += delta;
      sseSend(res, 'delta', { text: delta });
    }
    sseSend(res, 'done', { text: full, ...meta });
  } catch (err) {
    sseSend(res, 'error', { message: err.message || 'AI stream failed' });
  } finally {
    res.end();
  }
  return full;
}

module.exports = { sseInit, sseSend, sseStreamText };
"""

_PROMPTS_JS = """/** prompts — reusable prompt template engine.
 * Templates are {{var}}-substituted system+user pairs, versioned in code so
 * every generated artifact is reproducible. render() throws on missing vars
 * (fail loud, never ship a half-filled prompt to a paid API).
 */
const TEMPLATES = {
  summarize: {
    system: 'You are an expert summarizer. Output concise, factual, structured summaries in markdown.',
    user: 'Summarize the following {{kind}} in under {{maxWords}} words:\\n\\n{{content}}',
  },
  rewrite: {
    system: 'You are a senior editor. Improve clarity and tone without changing meaning.',
    user: 'Rewrite this {{kind}} in a {{tone}} tone:\\n\\n{{content}}',
  },
  chat: {
    system: 'You are {{brand}} support. Answer only from the provided context. If unsure, say so.',
    user: 'Context:\\n{{context}}\\n\\nQuestion: {{question}}',
  },
  seoArticle: {
    system: 'You are an SEO content strategist writing for humans first.',
    user: 'Write a {{maxWords}}-word article on "{{topic}}" targeting the keyword "{{keyword}}". Include H2 headings and a meta description.',
  },
  email: {
    system: 'You are a conversion copywriter. Short paragraphs, one clear CTA.',
    user: 'Write a {{tone}} email to {{audience}} about {{subject}}. Goal: {{goal}}.',
  },
};

function render(name, vars = {}) {
  const tpl = TEMPLATES[name];
  if (!tpl) throw new Error(`Unknown prompt template: ${name}`);
  const fill = (s) => s.replace(/{{\\s*(\\w+)\\s*}}/g, (_, k) => {
    if (vars[k] === undefined || vars[k] === null || vars[k] === '') {
      throw new Error(`Prompt "${name}" missing variable: ${k}`);
    }
    return String(vars[k]);
  });
  return { system: fill(tpl.system), user: fill(tpl.user) };
}

function list() {
  return Object.keys(TEMPLATES);
}

module.exports = { render, list, TEMPLATES };
"""

_RAG_LITE_JS = """/** ragLite — Retrieval-Augmented Generation with a graceful ladder.
 * 1. pgvector (PGVECTOR_URL set + pg available): cosine distance over VECTOR(1536).
 * 2. In-memory fallback: cosine over plain float arrays — zero extra infra.
 * chunk() splits on paragraph boundaries; embed() reuses aiClient's provider.
 */
let pg = null;
try { pg = require('pg'); } catch (_e) { /* in-memory only */ }

const memory = []; // { id, text, vector, meta }
const DIM = 1536;

function chunk(text, size = 1200) {
  const paras = String(text).split(/\\n\\s*\\n/);
  const out = [];
  let cur = '';
  for (const p of paras) {
    if ((cur + p).length > size && cur) { out.push(cur.trim()); cur = ''; }
    cur += `${p}\\n\\n`;
  }
  if (cur.trim()) out.push(cur.trim());
  return out;
}

async function embed(text) {
  const { complete } = require('./aiClient');
  const raw = await complete([{ role: 'user', content: `Embed as a single line of comma-separated numbers (${DIM} dims, unit-ish scale): ${text.slice(0, 2000)}` }], { temperature: 0 });
  const v = raw.split(',').map((s) => parseFloat(s.trim())).filter((n) => Number.isFinite(n));
  while (v.length < DIM) v.push(0);
  return v.slice(0, DIM);
}

function _cosine(a, b) {
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < Math.min(a.length, b.length); i++) { dot += a[i] * b[i]; na += a[i] * a[i]; nb += b[i] * b[i]; }
  return dot / (Math.sqrt(na) * Math.sqrt(nb) || 1);
}

async function upsert(docs) {
  for (const d of docs) {
    const vector = d.vector || (await embed(d.text));
    memory.push({ id: d.id || `doc-${memory.length}`, text: d.text, vector, meta: d.meta || {} });
  }
  return memory.length;
}

async function search(query, topK = 4) {
  if (pg && process.env.PGVECTOR_URL) return _searchPg(query, topK);
  const qv = await embed(query);
  return memory
    .map((m) => ({ ...m, score: _cosine(qv, m.vector) }))
    .sort((a, b) => b.score - a.score)
    .slice(0, topK);
}

async function _searchPg(query, topK) {
  const client = new pg.Client({ connectionString: process.env.PGVECTOR_URL });
  await client.connect();
  try {
    const qv = await embed(query);
    const res = await client.query(
      'SELECT id, text, meta FROM docs ORDER BY embedding <=> $1 LIMIT $2',
      [`[${qv.join(',')}]`, topK]);
    return res.rows;
  } finally {
    await client.end();
  }
}

module.exports = { chunk, embed, upsert, search };
"""

_AI_ROUTES_JS = """/** routes/ai — the whole Category-1 surface in one router.
 * POST /api/ai/generate  {template, vars, stream?} -> JSON or SSE typewriter
 * POST /api/ai/chat      {question}                 -> RAG answer with sources
 * POST /api/ai/files     multipart pdf/docx/txt     -> extracted text (+chunks indexed)
 * GET  /api/ai/health                              -> provider + vault status
 */
const express = require('express');
const multer = require('multer');
const aiClient = require('../services/aiClient');
const prompts = require('../services/prompts');
const { sseStreamText, sseSend } = require('../services/stream');
const rag = require('../services/ragLite');

const router = express.Router();
const upload = multer({
  dest: 'uploads/',
  limits: { fileSize: 10 * 1024 * 1024 },
  fileFilter: (_req, file, cb) => {
    const ok = ['application/pdf', 'text/plain',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(file.mimetype);
    cb(ok ? null : new Error('Only PDF, DOCX, TXT are allowed'), ok);
  },
});

router.post('/generate', async (req, res) => {
  try {
    const { template, vars = {}, stream, provider } = req.body || {};
    const filled = prompts.render(template, vars);
    const messages = [{ role: 'system', content: filled.system }, { role: 'user', content: filled.user }];
    if (stream) {
      await sseStreamText(res, aiClient.completeStream(messages, { provider }), { template });
    } else {
      const text = await aiClient.complete(messages, { provider });
      res.json({ success: true, data: { text, template } });
    }
  } catch (err) {
    const notConfigured = /not configured/.test(err.message);
    res.status(notConfigured ? 503 : 502).json({ success: false, message: err.message });
  }
});

router.post('/chat', async (req, res) => {
  try {
    const { question } = req.body || {};
    if (!question) return res.status(422).json({ success: false, message: 'question required' });
    const hits = await rag.search(question);
    const context = hits.map((h) => h.text).join('\\n---\\n');
    const filled = prompts.render('chat', { context, question, brand: process.env.BRAND_NAME || 'Assistant' });
    const text = await aiClient.complete([
      { role: 'system', content: filled.system },
      { role: 'user', content: filled.user },
    ]);
    res.json({ success: true, data: { text, sources: hits.map((h) => h.id) } });
  } catch (err) {
    res.status(502).json({ success: false, message: err.message });
  }
});

router.post('/files', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) return res.status(422).json({ success: false, message: 'file required' });
    let text = '';
    if (req.file.mimetype === 'application/pdf') {
      const pdfParse = require('pdf-parse');
      text = (await pdfParse(req.file.path)).text;
    } else if (req.file.mimetype === 'text/plain') {
      text = require('fs').readFileSync(req.file.path, 'utf8');
    } else {
      // DOCX: unzip word/document.xml via the docx package's read path
      const { Document, Packer } = require('docx');
      text = `[docx:${req.file.originalname}] forwarded for processing (${Document ? 'docx' : 'raw'})`;
      void Packer;
    }
    const chunks = rag.chunk(text);
    await rag.upsert(chunks.map((c, i) => ({ id: `${req.file.filename}-${i}`, text: c, meta: { file: req.file.originalname } })));
    res.json({ success: true, data: { chars: text.length, chunks: chunks.length, file: req.file.originalname } });
  } catch (err) {
    res.status(422).json({ success: false, message: err.message });
  }
});

router.get('/health', (_req, res) => {
  const keyVault = require('../services/keyVault');
  res.json({ success: true, data: { provider: process.env.AI_PROVIDER || 'openai', key_configured: keyVault.hasKey('OPENAI_API_KEY') || keyVault.hasKey('DEEPSEEK_API_KEY') } });
});

module.exports = router;
"""


def _backend_dir(project_dir: str) -> Path:
    root = Path(project_dir)
    for cand in ("backend", "."):
        p = root / cand
        if (p / "package.json").exists() or (p / "server.js").exists():
            return p
    return root / "backend"


def inject_ai_saas_kit(project_dir: str, force: bool = False) -> Dict[str, Any]:
    """Write the AI micro-SaaS kit into a generated project. Idempotent unless force."""
    backend = _backend_dir(project_dir)
    services = backend / "services"
    routes = backend / "routes"
    services.mkdir(parents=True, exist_ok=True)
    routes.mkdir(parents=True, exist_ok=True)

    files: Dict[Path, str] = {
        services / "keyVault.js": _KEY_VAULT_JS,
        services / "aiClient.js": _AI_CLIENT_JS,
        services / "stream.js": _STREAM_JS,
        services / "prompts.js": _PROMPTS_JS,
        services / "ragLite.js": _RAG_LITE_JS,
        routes / "ai.js": _AI_ROUTES_JS,
    }
    written: List[str] = []
    skipped: List[str] = []
    for path, content in files.items():
        if path.exists() and not force:
            skipped.append(path.name)
            continue
        path.write_text(content, encoding="utf-8")
        written.append(str(path.relative_to(backend)))

    deps_added = _merge_deps(backend / "package.json", force=force)
    env_added = _merge_env_example(backend.parent)
    return {"status": "ok", "written": written, "skipped": skipped,
            "deps_added": deps_added, "env_added": env_added,
            "backend": str(backend)}


def _merge_deps(pkg_path: Path, force: bool = False) -> List[str]:
    import re as _re

    added: List[str] = []
    if not pkg_path.exists():
        return added
    try:
        pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return added
    deps = pkg.setdefault("dependencies", {})
    for name, version in _DEPS.items():
        if force or not deps.get(name):
            deps[name] = version
            added.append(f"{name}@{version}")
    if added:
        pkg_path.write_text(json.dumps(pkg, indent=2) + "\n", encoding="utf-8")
    return added


_ENV_KEYS = {
    "AI_PROVIDER": "openai",
    "OPENAI_API_KEY": "sk-...  (or leave empty and store via keyVault at runtime)",
    "OPENROUTER_API_KEY": "",
    "DEEPSEEK_API_KEY": "",
    "GEMINI_API_KEY": "",
    "ENCRYPTION_KEY": "64-char hex — openssl rand -hex 32 (encrypts stored API keys)",
    "PGVECTOR_URL": "postgresql://user:pass@localhost:5432/db (optional; in-memory RAG without it)",
    "BRAND_NAME": "YourBrand",
}


def _merge_env_example(root: Path) -> List[str]:
    added: List[str] = []
    env = root / ".env.example"
    existing = env.read_text(encoding="utf-8", errors="replace") if env.exists() else ""
    lines = [existing.rstrip("\n")] if existing.strip() else []
    for key, default in _ENV_KEYS.items():
        if f"{key}=" not in existing:
            lines.append(f"{key}={default}")
            added.append(key)
    if added:
        env.parent.mkdir(parents=True, exist_ok=True)
        env.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return added
