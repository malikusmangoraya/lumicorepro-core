#!/usr/bin/env node
/**
 * cli.mjs — `npm run upgrade`
 *
 * Fast by construction: the cache lets unchanged apps be skipped after a few
 * stat() calls, so a routine run reads almost nothing. Adds `--json` for tooling
 * and `--dry-run` for a review pass that writes nothing.
 */
import { runUpgrade, listRules, discoverApps } from './engine.mjs';
import { selectRules } from './rules/index.mjs';

const HELP = `lumicore upgrade — cached, idempotent, parallel-safe app upgrades

Usage
  node scripts/upgrade/cli.mjs [options]

Options
  --apps a,b        only these app slugs
  --root <dir>      scan this root (repeatable; default products/sell-today, products)
  --only id,id      run only these rule ids
  --skip id,id      skip these rule ids
  --dry-run         plan and report, write nothing
  --force           ignore the cache and re-evaluate every app
  --json            machine-readable report on stdout
  --list            list discovered apps and exit
  --rules           list rule ids and exit
  --no-bootstrap    alias for --skip theme-bootstrap
  -h, --help        this text
`;

function parseArgs(argv) {
  const options = { apps: [], roots: [], only: [], skip: [], dryRun: false, force: false, json: false, list: false, rules: false };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = () => argv[++i];
    const values = (raw) => raw.split(',').map((value) => value.trim()).filter(Boolean);
    switch (arg) {
      case '--apps': options.apps.push(...values(next() || '')); break;
      case '--root': options.roots.push(next()); break;
      case '--only': options.only.push(...values(next() || '')); break;
      case '--skip': options.skip.push(...values(next() || '')); break;
      case '--no-bootstrap': options.skip.push('theme-bootstrap'); break;
      case '--dry-run': options.dryRun = true; break;
      case '--force': options.force = true; break;
      case '--json': options.json = true; break;
      case '--list': options.list = true; break;
      case '--rules': options.rules = true; break;
      case '-h':
      case '--help': options.help = true; break;
      default:
        throw new Error(`Unknown option: ${arg} (try --help)`);
    }
  }
  return options;
}

function ms(value) {
  return `${value < 10 ? value.toFixed(1) : Math.round(value)}ms`;
}

function printHuman(report) {
  console.log(`lumicore upgrade · ${report.rules.length} rules · ${report.totals.apps} apps`);
  for (const app of report.apps) {
    const state = app.cached ? 'cached' : app.outcome;
    const files = app.files.length ? app.files.map((file) => `${file.status === 'created' ? '+' : '~'}${file.path}`).join(' ') : '—';
    console.log(`  ${app.id.padEnd(18)} ${state.padEnd(8)} ${ms(app.ms).padStart(7)}  ${files}`);
    for (const note of app.notes) console.log(`      note: ${note}`);
    if (app.outcome === 'error') console.log('      ^ reported as error, not a pass');
  }
  const { files, skipped, clean, review, errors } = report.totals;
  console.log(
    `totals: ${files} files changed · ${clean} already clean · ${skipped} skipped from cache · ${review} need review · ${errors} errors · ${ms(report.elapsedMs)} total`
  );
}

function main() {
  let options;
  try {
    options = parseArgs(process.argv.slice(2));
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
    return;
  }

  if (options.help) {
    console.log(HELP);
    return;
  }

  let rules;
  try {
    rules = selectRules(options);
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
    return;
  }

  if (options.rules) {
    for (const rule of listRules(rules)) console.log(`${rule.id}@${rule.version}  ${rule.title}`);
    return;
  }

  if (options.list) {
    for (const app of discoverApps(options)) console.log(`${app.id.padEnd(20)} ${app.dir}`);
    return;
  }

  const report = runUpgrade({ rules, options });
  if (options.json) console.log(JSON.stringify(report, null, 2));
  else printHuman(report);

  if (report.totals.errors) process.exitCode = 1;
}

main();
