/**
 * rules/index.mjs — the rule registry.
 *
 * A rule is a plain object:
 *   { id, version, title, watch: string[], plan(ctx) -> Op[] }
 *
 * `plan` must be pure and idempotent: it reads through ctx.get(), returns
 * operations, and never touches the filesystem itself. Bump a rule's `version`
 * when its output changes — the version is part of the cache fingerprint, so a
 * bump is what tells the engine to re-evaluate every app.
 */
import designTokens from './design-tokens.mjs';
import tailwindTheme from './tailwind-theme.mjs';
import themeController from './theme-controller.mjs';
import themeBootstrap from './theme-bootstrap.mjs';
import uiPrimitives from './ui-primitives.mjs';

const ALL = [designTokens, tailwindTheme, themeController, themeBootstrap, uiPrimitives];

export function selectRules({ only = [], skip = [] } = {}) {
  const wanted = only.length ? new Set(only) : null;
  const ignored = new Set(skip);
  const selected = ALL.filter((rule) => (wanted ? wanted.has(rule.id) : true) && !ignored.has(rule.id));

  if (wanted && selected.length !== wanted.size) {
    const known = new Set(ALL.map((rule) => rule.id));
    const unknown = [...wanted].filter((id) => !known.has(id));
    throw new Error(`Unknown rule id(s): ${unknown.join(', ')}. Known: ${[...known].join(', ')}`);
  }
  return selected;
}

export default ALL;
