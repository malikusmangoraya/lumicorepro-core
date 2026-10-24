# Optional Reflex Project Generation — Design Specification

**Status:** Draft for review  
**Date:** 2026-10-22

## Goal

Add an opt-in Reflex/Python web-app output mode to LumicorePro without changing existing React/Vite generation or claiming that an unverified Reflex project is production-ready.

## Current context

LumicorePro's current agent generates React/Vite frontends, Express backends, and related artifacts through its orchestration and project-builder paths. A separate `FullStackUltraEngine` also generates React/Vite + Express + PostgreSQL. No Reflex dependency or implementation was found in the agent requirements or repository search. Reflex documentation and the upstream repository could not be fetched in the current BYOK environment, so exact currently supported versions, runtime/deploy constraints, and license details remain to be independently confirmed before implementation adds dependencies.

## Design

- Add an explicit project mode (for example `reflex`) selected by a request/CLI option. The existing default remains React/Vite and must produce the same mode and output contract as before.
- Keep Reflex generation in a dedicated module with a small interface used by the orchestrator; do not embed a second UI runtime in the existing React generator.
- Generate a minimal, runnable Reflex app, its Python dependency declaration, and a README with setup/run instructions. Do not fabricate database, auth, payments, deploy adapters, or credentials.
- Treat Reflex as an optional dependency: normal LumicorePro install and React mode must work without it. If Reflex mode is selected without the dependency, return an actionable, mode-specific error rather than silently falling back to React.
- Validate generated files and execute the narrowest real Reflex check available in the environment. A passing static test or package import alone is not evidence that the app launches. If the dependency/runtime is unavailable, report that limitation and do not mark end-to-end validation complete.
- Confirm upstream package identity, license, supported Python versions, installation method, and project launch command from authoritative upstream sources before pinning or documenting them. No internet verification has succeeded yet; dependency addition is gated on this check.

## Acceptance criteria

1. No mode option continues to generate the established React/Vite project.
2. Explicit Reflex mode produces a separate, minimal Reflex project and does not create React/Vite artifacts unless specifically required by the confirmed upstream setup.
3. Selecting Reflex without its optional dependency fails clearly and does not produce a misleading successful result.
4. Generated project files pass structural checks and, where dependencies/runtime are available, the generated app starts or passes Reflex's authoritative validation command.
5. Tests cover default-mode non-regression, explicit mode selection, missing optional dependency, and generated output structure.
6. Documentation makes no unsupported claims about production deployment, security, or supported Reflex versions.

## Out of scope

- Replacing or migrating the default React/Vite generator.
- Automatically installing dependencies into a user's global Python environment.
- Adding Reflex-specific hosted services, authentication, databases, or deployment without separate provider research and approval.
- Claiming production readiness based solely on scaffold generation.
