"""Enterprise extension services for the LumicorePro AI agent.

Self-contained, add-on capabilities that extend the delivery pipeline:
marketing kit auto-generation, real-browser QA, watchtower analytics,
Stripe checkout scaffolding and element-level visual editing.

Every module is defensive: it degrades gracefully and never blocks the
core pipeline when an optional dependency (PIL, Playwright, git, etc.)
is unavailable.
"""