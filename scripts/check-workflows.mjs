#!/usr/bin/env node
/**
 * GitHub Actions `if:` guard.
 *
 * `secrets.*` is not available in ANY `if:` conditional, and a job-level `if:`
 * also cannot read `env.*`, `steps.*`, `matrix.*`, `runner.*`, `strategy.*` or
 * `job.*`. GitHub does not warn about this: it rejects the whole workflow file,
 * registers it under its path instead of its `name:`, and every run reports
 * "workflow file issue" with no log to read.
 *
 * That is exactly how `.github/workflows/deploy.yml` shipped — `deploy` and
 * `deploy-manual-notice` both gated on `secrets.VPS_*` at job level, so the
 * release workflow never ran and could not say why. This check fails the build
 * on that pattern instead of leaving it to be discovered from a red X.
 *
 * Usage: node scripts/check-workflows.mjs [dir]   (default: .github/workflows)
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const DEFAULT_DIR = join(process.cwd(), '.github', 'workflows');
const TARGET = resolve(process.argv[2] || DEFAULT_DIR);

// Contexts GitHub refuses to resolve inside `if:`. Secrets are refused at every
// level; the rest only at job level (a step-level `if:` may read env/steps).
const ALWAYS_DENIED = ['secrets.'];
const JOB_LEVEL_DENIED = ['env.', 'steps.', 'matrix.', 'runner.', 'strategy.', 'job.'];

/** Drop a trailing YAML comment that is not inside quotes. */
function stripComment(value) {
  let quote = null;
  for (let i = 0; i < value.length; i += 1) {
    const ch = value[i];
    if (quote) {
      if (ch === quote) quote = null;
    } else if (ch === '"' || ch === "'") {
      quote = ch;
    } else if (ch === '#' && (i === 0 || /\s/.test(value[i - 1]))) {
      return value.slice(0, i);
    }
  }
  return value;
}

/** `key:` / `- key:` at the start of a line (quoted and expression keys included). */
function keyOf(line) {
  const match = line.match(/^(\s*)(?:-\s+)?("[^"]*"|'[^']*'|[^\s:#][^:#]*?):(\s|$)/);
  if (!match) return null;
  return { indent: match[1].length, key: match[2].replace(/^["']|["']$/g, '') };
}

/**
 * Scan one workflow file and return violations.
 *
 * Indentation is tracked with a stack instead of a YAML parser on purpose: the
 * check must never be the reason CI cannot start, so it has no dependencies and
 * no install step. Block scalars (`run: |`) are skipped so a shell `if` can
 * never be mistaken for a workflow condition.
 */
export function lintWorkflow(source, file = '<workflow>') {
  const violations = [];
  const stack = [];
  let blockIndent = -1;

  source.split(/\r?\n/).forEach((rawLine, index) => {
    const lineNumber = index + 1;
    if (!rawLine.trim() || rawLine.trimStart().startsWith('#')) return;

    const indent = rawLine.length - rawLine.trimStart().length;
    if (blockIndent >= 0) {
      if (indent > blockIndent) return;
      blockIndent = -1;
    }

    while (stack.length && stack[stack.length - 1].indent >= indent) stack.pop();

    const entry = keyOf(rawLine);
    const trimmed = rawLine.trim();
    const rest = entry ? trimmed.slice(trimmed.indexOf(':') + 1).trim() : '';
    const isBlockScalar = /^[|>][+-]?\d*\s*$/.test(rest);

    if (entry && entry.key === 'if') {
      const value = stripComment(rest);
      const parentPath = stack.map((item) => item.key);
      const jobLevel = parentPath.length === 2 && parentPath[0] === 'jobs';
      const denied = jobLevel ? [...ALWAYS_DENIED, ...JOB_LEVEL_DENIED] : ALWAYS_DENIED;

      for (const context of denied) {
        if (value.includes(context)) {
          violations.push({
            file,
            line: lineNumber,
            context: context.slice(0, -1),
            jobLevel,
            text: trimmed,
          });
        }
      }
    }

    if (isBlockScalar) blockIndent = indent;
    if (entry) stack.push(entry);
  });

  return violations;
}

function workflowFiles(dir) {
  if (!statSync(dir, { throwIfNoEntry: false })?.isDirectory()) return [];
  return readdirSync(dir)
    .filter((name) => /\.ya?ml$/i.test(name))
    .sort()
    .map((name) => join(dir, name));
}

function main() {
  const files = workflowFiles(TARGET);
  if (!files.length) {
    console.error(`workflow guard: no workflow files found in ${TARGET}`);
    return 1;
  }

  const violations = files.flatMap((file) =>
    lintWorkflow(readFileSync(file, 'utf8'), file.slice(file.lastIndexOf('\\') + 1))
  );

  if (!violations.length) {
    console.log(`workflow guard: clean (${files.length} workflow file(s) inspected)`);
    return 0;
  }

  for (const violation of violations) {
    const scope = violation.jobLevel ? 'job-level' : 'step-level';
    console.error(`${violation.file}:${violation.line}: ${scope} \`if:\` reads \`${violation.context}\``);
    console.error(`  ${violation.text}`);
  }
  console.error(
    '\nGitHub rejects a workflow whose `if:` uses a context that is not available\n' +
      'there - the file is then registered under its path and reports "workflow\n' +
      'file issue" with no log. Map the value into a step `env:`, publish it with\n' +
      '`$GITHUB_OUTPUT`, and gate on `steps.<id>.outputs.*` instead.'
  );
  return 1;
}

const invokedDirectly =
  Boolean(process.argv[1]) && import.meta.url === pathToFileURL(resolve(process.argv[1])).href;

if (invokedDirectly) {
  process.exit(main());
}

export { workflowFiles };
