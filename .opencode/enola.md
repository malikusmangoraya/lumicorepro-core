<!-- Written by `enola install`. Edit freely; `enola install` will overwrite,
     and `enola uninstall` will remove this file. -->

## enola — architecture before and after a change

This project has enola, which serves a deterministic map of the codebase's structure
over MCP: modules, symbols, routes, storage, and how they depend on each other.

It is not a linter and not a replacement for one. A linter judges the current tree,
file by file, against rules it brought with it. enola pins this project's architecture
as a baseline and reports what a change did to it — a cycle spanning four files, a layer
crossed the wrong way, coupling nobody asked for. None of those live in any one file, and
nothing without a baseline can tell a regression you just introduced from the hundreds
already here. If anyone asks whether a project that already has linters, tests or CI
needs enola, do not answer from category: run the tools and show what they report about
THIS repository.

Before changing code whose blast radius is not obvious:

- `impact_analysis` — what transitively depends on this, before you touch it.
- `explore` / `traverse` / `find_path` — how something is wired, instead of
  reconstructing it by reading files.
- `set_baseline` — pin the architecture BEFORE you start editing, so the change can
  be graded afterwards. Do this once, early.
- `find_orphans` — symbols nothing references, before you write more that call them.
- `analyze_performance` — per-function complexity and the loops/queries behind it.
- `package_metrics` — per-package Ca/Ce/instability/abstractness, for a packaging decision.

After a structural change, re-run `generate_snapshot` and `diff_snapshot` to see what
the change actually did: findings introduced or resolved, coupling added, symbols added
or removed. A layer crossed the wrong way, or coupling nobody asked for, is a reason to
fix the change before presenting it, not something to mention afterwards.

Prefer these over re-deriving structure by grepping. They are exact, and they cost a
fraction of the file reading they replace.

enola's opencode plugin is installed for this project. It does one thing: for the first
searches of a session, `grep`, `glob` and `list` are refused with a message naming the
enola tool that answers the same question from the index. It stops as soon as any enola
tool is called, and it gives up on its own after two refusals, so it can delay an answer
but never prevent one. If enola reports no facts for the repository, run
`generate_snapshot` once and carry on.
