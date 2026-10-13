// Phase 0 secret-hygiene classification — read-only.
// Reports file path + variable NAME + a confidence bucket. It never prints or
// persists any variable VALUE, and never writes values to disk.
import fs from 'node:fs';
import path from 'node:path';

const SECRET_NAME = /(SECRET|PASS(WORD)?|TOKEN|API_KEY|_KEY$|PRIVATE|LICENSE|CREDENTIAL|DATABASE_URL|REDIS_URL|SMTP_USER|EMAIL_USER|EMAIL_HOST)/i;

const DEV_DEFAULT = [
  'change', 'changeme', 'replace', 'example', 'placeholder', 'your_', 'your-',
  'xxx', 'dummy', 'todo', 'dev', 'test', 'localhost', '127.0.0.1', 'secret123',
  'password123', 'admin', 'root', 'minioadmin', 'postgres',
];

const looksPlaceholder = (value) => {
  const v = String(value).trim();
  if (!v) return true;
  const lower = v.toLowerCase();
  if (DEV_DEFAULT.some((m) => lower.includes(m))) return true;
  if (/^<.*>$/.test(v)) return true;
  if (/^(true|false|null|none|auto|\d+)$/i.test(v)) return true;
  return false;
};

// Confidence that a value is a real, usable credential rather than a dev default.
const confidence = (value) => {
  const v = String(value).trim();
  if (looksPlaceholder(v)) return 'placeholder-or-dev-default';
  const classes = [/[a-z]/, /[A-Z]/, /\d/, /[^A-Za-z0-9]/].filter((r) => r.test(v)).length;
  if (v.length >= 24 && classes >= 3) return 'high';
  if (v.length >= 16 && classes >= 2) return 'medium';
  return 'low';
};

const parseEnv = (text) => {
  const vars = [];
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith('#')) continue;
    const m = line.match(/^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/);
    if (!m) continue;
    let value = m[2].trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    vars.push({ name: m[1], value });
  }
  return vars;
};

const collect = () => {
  const found = [];
  const walk = (dir, depth) => {
    if (depth > 4) return;
    let entries = [];
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const e of entries) {
      if (['node_modules', '.git', 'dist', 'venv', '__pycache__'].includes(e.name)) continue;
      const full = path.join(dir, e.name);
      if (e.isDirectory()) walk(full, depth + 1);
      else if (e.name === '.env' || /^\.env\.(production|staging|development|local)$/.test(e.name)) found.push(full);
    }
  };
  walk('.', 0);
  return found;
};

const results = [];
for (const file of collect()) {
  let text = '';
  try {
    text = fs.readFileSync(file, 'utf8');
  } catch {
    continue;
  }
  const secretVars = parseEnv(text)
    .filter((v) => SECRET_NAME.test(v.name))
    .map((v) => ({ name: v.name, confidence: confidence(v.value) }));
  results.push({ file: file.split(path.sep).join('/'), secret_variables: secretVars });
}

const interesting = results.filter(
  (r) => r.secret_variables.some((v) => v.confidence === 'high' || v.confidence === 'medium'),
);

fs.mkdirSync('.superpowers/phase0', { recursive: true });
fs.writeFileSync(
  '.superpowers/phase0/secret-hygiene.json',
  JSON.stringify({ generated_at: new Date().toISOString(), note: 'Names and confidence buckets only; no values stored.', files: results }, null, 2),
);

console.log('env-like files inspected:', results.length);
console.log('files with medium/high-confidence secret-named variables:', interesting.length);
for (const r of interesting) {
  const counts = r.secret_variables.reduce((a, v) => ((a[v.confidence] = (a[v.confidence] || 0) + 1), a), {});
  const names = r.secret_variables.filter((v) => v.confidence !== 'placeholder-or-dev-default').map((v) => v.name);
  console.log(`- ${r.file} :: ${JSON.stringify(counts)} :: ${names.join(', ')}`);
}
