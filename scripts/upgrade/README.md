# Lumicore upgrade engine

A cached, idempotent upgrade runner for the product apps in this monorepo.
It exists so that a routine upgrade pass costs a few `stat()` calls instead of
re-reading every app, and so that each upgrade is described as a rule rather
than repeated by hand.

```bash
npm run upgrade              # apply, skipping apps the cache proves unchanged
npm run upgrade:check        # plan and report only (no writes)
npm run upgrade -- --json    # machine-readable report
npm run upgrade -- --apps aurelia-estates,resupro --force
```

## How the speed works

| Layer | What it avoids |
| --- | --- |
| Rule fingerprint | Re-planning apps when the rule set itself has not changed |
| Per-app signature | Re-reading source when the watched files' `mtime`/`size` are unchanged |
| Single read per file | Rules share one read through `ctx.get()`; the file is never opened twice |
| Content equality check | Writing a file whose bytes would not change |
| Manifest in `node_modules/.cache` | Touching `.gitignore` or the repository for cache state |

An app is skipped only when **both** the rule fingerprint and the watched-file
signature match the previous successful run, and that run was not an error. A
`--force` run or a rule `version` bump re-evaluates everything.

## Rules

| id | version | Target | Effect |
| --- | --- | --- | --- |
| `design-tokens` | 1.0.0 | `src/index.css` | `[data-theme]` `color-scheme` support + token-driven `:focus-visible` ring |
| `tailwind-theme` | 1.0.0 | `tailwind.config.js` | `darkMode: ['class', '[data-theme="dark"]']` so `dark:` responds to the attribute |
| `theme-controller` | 1.0.0 | `src/lib/theme.js` | `.dark` + `data-theme`, `?theme=` param, `setTheme`/`toggleTheme` API; brand token exports re-emitted verbatim |
| `theme-bootstrap` | 1.0.0 | `index.html` | Pre-paint inline theme resolution (no dark-first flash); skipped under a CSP |
| `ui-primitives` | 1.0.0 | `src/shared/ui/*` | Token-driven `Button` / `Badge` / `Card` + barrels, ARIA correct, no new dependencies |

## Writing a rule

```js
export default {
  id: 'my-rule',
  version: '1.0.0',
  title: 'One line describing the effect',
  watch: ['src/index.css'],          // drives the cache signature
  plan(ctx) {
    const css = ctx.get('src/index.css');   // cached read, null when absent
    if (css === null || css.includes('MY_MARKER')) return [];   // idempotent
    return [{ kind: 'update', path: 'src/index.css', content: next(css) }];
  },
};
```

Contract:

- `plan` is pure and idempotent — it returns operations, the engine writes them.
- Operation kinds: `create`, `update`, `remove`, or `skip` (with a `note`).
- Always gate on a marker or an exact-content check, so a second run is a no-op.
- Never rewrite brand-owned data. `theme-controller` shows the pattern: detect
  the per-brand exports and carry them over untouched.
- Bump `version` whenever the generated output changes; that is what invalidates
  the cache for the rule.
- Use `ctx.note()` when a rule deliberately does nothing, so "not applicable" is
  reported rather than silently passing.

Registered in [rules/index.mjs](scripts/upgrade/rules/index.mjs).

## Verification expectations

A rule run is a plan, not a proof. After an upgrade pass, build and smoke-test
the affected apps; the engine reports what it wrote, not that the app still works.
