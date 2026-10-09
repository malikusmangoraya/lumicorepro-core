# Lumicore Website Prompting Suite Design

**Status:** Proposed for review

## Purpose

Make Lumicore's existing website-generation standards easy to use. A user should
be able to describe a product, audience, and business goal, then give an AI a
clear brief that leads to a distinctive, usable, responsive website instead of
an interchangeable template.

## Audience and success

The primary audience is a Lumicore user or developer who wants to commission a
website from an AI but is unsure what details to specify. The documentation is
successful when that reader can:

- Choose what information to provide without already knowing design jargon.
- Copy and adapt a prompt for a real website request.
- Ask for a visual direction that fits the brand and differs from generic or
  prior designs.
- Require working, relevant user journeys and honest quality verification.
- Make a focused follow-up request without asking the generator to rebuild
  unrelated parts.

## Current gap

`project-rules/MASTER_PROMPT.md` and `docs/UNIQUE_PROJECT_PLAYBOOK.md` already
cover strategy, design, implementation, and QA in depth. They do not provide a
single beginner-friendly prompt workflow and reusable brief template. The
master prompt names MySQL, while the root agent instructions and system
standards name PostgreSQL; the documentation must align with the active
backend implementation and governing repository instructions.

## Proposed document set

### `docs/WEBSITE_PROMPTING_GUIDE.md`

A practical how-to guide that explains the request workflow and contains:

- A short checklist of required project details, with plain-language
  descriptions and a clear way to mark unknowns.
- A copy-ready master prompt with fill-in fields for business, audience,
  brand, goals, pages, content, functionality, visual direction, assets,
  constraints, and delivery.
- A short prompt for users who want to start quickly, with explicit follow-up
  questions for important missing requirements.
- Small, distinct example prompts for different website types (for example,
  SaaS, ecommerce, and portfolio/local business).
- Iteration prompts for changing a specific area, preserving approved work,
  and reporting what was actually tested.
- A final acceptance checklist covering originality, responsive behavior,
  accessibility, working interactions, performance, and evidence-based QA.

The guide will state that prompts may be written in English or Urdu/Roman
Urdu, while emphasizing that names, features, constraints, and business facts
must remain explicit. It will not imply that prompt length alone guarantees
quality.

### `docs/WEBSITE_DESIGN_BRIEF_TEMPLATE.md`

A standalone fillable project brief that can be completed before generation.
It will capture the same decisions as the guide's prompt fields, plus explicit
open questions, non-goals, reference-to-original-attribute translations,
responsive/reduced-motion requirements, and acceptance criteria. It will be
usable as a Markdown file copied into a generated project or attached to a
generation request; it will not introduce a new runtime format or pipeline.

### Existing authoritative guidance

- `project-rules/MASTER_PROMPT.md`: add the prompt-input contract, explain how
  to resolve missing or conflicting requirements, and require a concise
  project brief/design direction before implementation. Align its stack
  description with the active repository configuration and instructions
  (PostgreSQL is the documented default unless the implementation shows
  otherwise).
- `docs/UNIQUE_PROJECT_PLAYBOOK.md`: link the practical guide and brief,
  clarify how to compare design directions using distinct design decisions,
  and keep its originality and measurable QA rules authoritative.
- `docs/index.md`: add an easy-to-find entry point linking the guide, brief,
  master prompt, and unique-project playbook.

Existing in-depth rules remain the source of truth; the new documents explain
how to apply those rules and must not create competing standards.

## User flow

1. Start at the documentation index and open the prompting guide.
2. Fill the design brief, or use the short prompt to discover missing details.
3. Submit the completed brief with the copy-ready prompt.
4. The generator follows the existing master workflow and records key design
   decisions before implementation.
5. Review the generated result against the acceptance checklist and request
   scoped changes using the iteration prompts.

## Design and content requirements

- The project identity must come from its audience, product, brand, and
  content, not from decoration alone.
- Ask for a small number of meaningfully different directions when the user
  has not specified one; explain the distinguishing decisions, then proceed
  with the selected or best-supported direction.
- References are inspiration attributes, never instructions to copy another
  site's exact composition, assets, or branding.
- Specify real, relevant interactions and their loading, empty, error,
  success, and recovery states where applicable. Do not invent business facts,
  reviews, metrics, assets, or functionality.
- Treat mobile, keyboard access, reduced motion, accessibility, performance,
  and SEO as requirements, not optional visual polish.
- Report tests and measurements only when they actually ran; mark the rest as
  not measured.
- Follow current repository instructions and inspect the project's actual
  package/configuration before choosing dependencies or backend technology.

## Out of scope

- Rewriting the generation pipeline, orchestrator, agents, or quality-gate
  implementation.
- Adding dependencies or changing website-generation behavior in code.
- Rewriting every prompt or documentation file in the repository.
- Changing secrets, environment files, or generated customer projects.
- Claiming every requested site needs 3D, animations, a backend, or a fixed
  page/section list.

## Documentation validation

- Confirm every new and changed Markdown link resolves to a repository file.
- Check that the prompt guide, brief, master prompt, and playbook agree on the
  workflow and point to one another appropriately.
- Check stack wording against `AGENTS.md`, system standards, and active
  backend configuration; use PostgreSQL as the documented default unless
  the implementation or a specific project requires otherwise.
- Review the copy-ready templates as a new user: required fields are clear,
  unknowns can be stated, and no prompt asks the user to provide secrets.
- Inspect the final diff to confirm only the agreed documentation files
  changed.