/** aiClient — one client, four providers, zero lock-in.
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
  const body = { model: opts.model || cfg.model, messages, stream: Boolean(opts.stream), temperature: opts.temperature ?? 0.7 };
  if (opts.maxTokens) body.max_tokens = opts.maxTokens;
  return JSON.stringify(body);
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
    const lines = buf.split('\n');
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
