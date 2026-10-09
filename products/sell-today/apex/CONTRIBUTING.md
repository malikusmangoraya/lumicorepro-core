# Contributing

Thank you for helping improve this project.

## Getting set up

```bash
git clone <your-fork-url>
cd apex
docker compose up -d          # PostgreSQL + Redis + API
cd frontend && npm ci && npm run dev
```

## Before you open a pull request

```bash
cd frontend && npm ci && npm run build     # must succeed
cd ../backend  && npm ci && npm start      # must boot and answer /health
```

CI runs the same checks, plus a parse check across every backend module and a
live probe of the health endpoint. A pull request cannot merge while any of
them fail.

## Commit messages

Use the imperative mood and keep the subject under 72 characters:

```
Add rate limiting to the password-reset endpoint
Fix timezone handling in recurring billing
```

## Code style

* Match the surrounding code. Consistency beats novelty.
* No commented-out code — delete it; version control remembers it.
* Every new endpoint validates its input and returns the standard error shape.
* New user-facing strings go into the i18n locale files, never inline.

## Reporting bugs

Open an issue with what you expected, what happened, and the smallest
reproduction you can manage. For security issues, follow `SECURITY.md` instead.

## Licence

Contributions are accepted under the terms in `LICENSE.md`.
