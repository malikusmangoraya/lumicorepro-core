# Orbitboard

A React product preview with an interactive sample roadmap and optional
Supabase-backed account authentication. Roadmap, team, admin, billing, and contact
submission features are not implemented; the sample roadmap resets in the current
page.

## Requirements

Install the app dependencies from the repository root:

```powershell
npm ci --prefix delivery\orbitboard\app
```

## Commands

Run these from the repository root:

```powershell
npm --prefix delivery\orbitboard\app run dev
npm --prefix delivery\orbitboard\app test
npm --prefix delivery\orbitboard\app run test:e2e
npm --prefix delivery\orbitboard\app run build
npm --prefix delivery\orbitboard\app run preview
```

The app's default base path is `/lumicorepro-core/orbitboard/`. For local development,
open `http://127.0.0.1:5173/lumicorepro-core/orbitboard/`. Override the path using
`VITE_BASE_PATH` when the deployment URL differs. The build is written to
`delivery/orbitboard/app/dist/`; it does not replace the legacy
`delivery/orbitboard/dist/` export. The build also writes a GitHub Pages `404.html`
fallback for client-side routes.

## Authentication setup

Copy `.env.example` to `.env.local` for local development and set:

- `VITE_SUPABASE_URL`: the Supabase project URL.
- `VITE_SUPABASE_ANON_KEY`: the project's public anonymous/publishable key only.

Never use a Supabase `service_role` or secret key in this frontend. Configure Supabase
email/password auth, email delivery, and the site's allowed redirect URLs for
`/lumicorepro-core/orbitboard/account` and
`/lumicorepro-core/orbitboard/reset-password`. The app uses PKCE, persisted sessions,
email verification, and password recovery. Without both public settings, account
routes show an explicit provider-setup notice and do not render a credential form.

For CI and deployment, provide the same two public values as GitHub Actions
repository variables named `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`. These
values are public by design; row/data secrets must never be embedded in the site.
The current app does not store roadmap data in Supabase.

## Publishing

The live app is published at
`https://malikusmangoraya.github.io/lumicorepro-core/orbitboard/`. The existing Apex
homepage remains at the domain root. The `Orbitboard CI and Pages deploy` workflow
verifies the app, then replaces only `gh-pages/orbitboard/`; it does not change the
root homepage or other Pages content.

On pushes to `master`, the workflow rebuilds and publishes this app. It can also be
started manually from GitHub Actions. Add `VITE_SUPABASE_URL` and
`VITE_SUPABASE_ANON_KEY` as repository Actions variables to enable real account
authentication in the published build. Until those public settings are configured,
the live account routes show the setup notice and do not accept credentials. The
build emits static entry files for each app route so direct links and refreshes work
without taking over the Apex site's root `404.html`.
