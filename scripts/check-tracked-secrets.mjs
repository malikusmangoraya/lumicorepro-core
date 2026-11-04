#!/usr/bin/env node
// Fail the build when a credential is committed.
//
// `.gitignore` only protects files that are not already tracked: once an
// env file is in the index, every later edit keeps it there and every clone
// gets the secret. This guard looks at what git actually tracks, parses the
// env files it finds, and fails on a secret-named variable holding anything
// that is not obviously a placeholder.
//
// VITE_* variables are skipped on purpose: Vite inlines them into the client
// bundle, so they are public by definition and must never hold a secret.
//
// Usage: node scripts/check-tracked-secrets.mjs
//        node scripts/check-tracked-secrets.mjs --all   (scan the working tree)

import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = path.resolve(new URL('..', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const SCAN_WORKTREE = process.argv.includes('--all');

const ENV_FILE = /(^|\/)\.env(\.[^/]+)?$/;
const EXAMPLE = /(\.example|\.sample|\.template)$/;
const SECRET_NAME =
  /(SECRET|PASS(WORD)?|TOKEN|API_KEY|_KEY$|PRIVATE|CREDENTIAL|DATABASE_URL|REDIS_URL|DSN)/i;

// A value is a placeholder only when the whole value is one. Substring matching
// is wrong in both directions: `postgresql://` is a scheme, not the word
// "postgres", and a random secret can contain "change" by chance.
const DEV_DEFAULTS = new Set([
  'change', 'changeme', 'change_me', 'change-me', 'replace', 'replace_me',
  'replace-me', 'example', 'placeholder', 'dummy', 'todo', 'redacted',
  'secret', 'password', 'postgres', 'minioadmin', 'admin', 'root', 'none',
  'null', 'auto', 'secret123', 'password123',
]);
const DEV_PREFIX =
  /^(your[_-]|change[_-]?me|replace[_-]?me|example|placeholder|dummy|todo|fill[_-]?me|xxx|<)/i;
const DEV_URL_HOST = /(localhost|127\.0\.0\.1|example\.com|\.example\b|\.invalid\b)/i;
const DEV_URL_CREDS = /:\/\/(user|username|admin|postgres|root):(pass|password|secret|changeme)@/i;

function isPlaceholder(value) {
  const v = String(value).trim().replace(/^["']|["']$/g, '');
  if (!v) return true;
  if (/^<.*>$/.test(v)) return true;
  if (/^\$\{?[A-Z0-9_]+\}?$/.test(v)) return true; // ${VAR} interpolation
  if (/^(true|false|null|none|auto|\d+)$/i.test(v)) return true;
  if (v.length < 8) return true;
  const lower = v.toLowerCase();
  if (DEV_DEFAULTS.has(lower)) return true;
  if (DEV_PREFIX.test(lower)) return true;
  if (lower.includes('://')) {
    if (DEV_URL_HOST.test(lower)) return true;
    if (DEV_URL_CREDS.test(lower)) return true;
  }
  return false;
}

function trackedEnvFiles() {
  if (SCAN_WORKTREE) {
    const found = [];
    const walk = (dir) => {
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        if (entry.name === 'node_modules' || entry.name === '.git') continue;
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) walk(full);
        else if (ENV_FILE.test(full.replace(/\\/g, '/').slice(ROOT.length + 1))) found.push(full);
      }
    };
    walk(ROOT);
    return found;
  }
  // GIT_BIN exists because some Windows machines block the PATH git binary by
  // application-control policy while a bundled git still works.
  const git = process.env.GIT_BIN || 'git';
  let out;
  try {
    out = execFileSync(git, ['ls-files', '-z'], { cwd: ROOT, encoding: 'utf8' });
  } catch (err) {
    console.error(`secret guard: cannot list tracked files (${err.message.split('\n')[0]})`);
    console.error('Set GIT_BIN to a working git executable, or run with --all.');
    process.exit(2);
  }
  return out
    .split('\0')
    .filter(Boolean)
    .filter((rel) => ENV_FILE.test(rel) && !EXAMPLE.test(rel))
    .map((rel) => path.join(ROOT, rel));
}

function scan(file) {
  const rel = path.relative(ROOT, file).replace(/\\/g, '/');
  const findings = [];
  let text;
  try {
    text = fs.readFileSync(file, 'utf8');
  } catch {
    return findings;
  }
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith('#')) continue;
    const match = line.match(/^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/);
    if (!match) continue;
    const [, name, value] = match;
    if (name.startsWith('VITE_')) continue; // public by design
    if (!SECRET_NAME.test(name)) continue;
    if (isPlaceholder(value)) continue;
    findings.push({ file: rel, name, length: value.trim().length });
  }
  return findings;
}

const files = trackedEnvFiles();
const findings = files.flatMap(scan);

if (findings.length === 0) {
  console.log(`secret guard: clean (${files.length} env file(s) inspected)`);
  process.exit(0);
}

console.error('secret guard: FAILED - credentials are committed\n');
for (const f of findings) {
  // Name and length only. Never print the value.
  console.error(`  ${f.file}: ${f.name} (${f.length} chars, non-placeholder)`);
}
console.error(
  '\nUntrack the file (git rm --cached), rotate the credential, and purge it from\n' +
    'history. A tracked secret stays readable in every clone even after a later\n' +
    'commit deletes it.'
);
process.exit(1);
