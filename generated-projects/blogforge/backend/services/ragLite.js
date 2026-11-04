/** ragLite — Retrieval-Augmented Generation with a graceful ladder.
 * 1. pgvector (PGVECTOR_URL set + pg available): cosine distance over VECTOR(1536).
 * 2. In-memory fallback: cosine over plain float arrays — zero extra infra.
 * chunk() splits on paragraph boundaries; embed() reuses aiClient's provider.
 */
let pg = null;
try { pg = require('pg'); } catch (_e) { /* in-memory only */ }

const memory = []; // { id, text, vector, meta }
const DIM = 1536;

function chunk(text, size = 1200) {
  const paras = String(text).split(/\n\s*\n/);
  const out = [];
  let cur = '';
  for (const p of paras) {
    if ((cur + p).length > size && cur) { out.push(cur.trim()); cur = ''; }
    cur += `${p}\n\n`;
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
