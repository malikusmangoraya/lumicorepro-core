# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — initial release

### Added
- Responsive, accessible user interface with a complete design system.
- Full internationalisation across 14 languages, including right-to-left
  layouts for Arabic and Urdu, and locale-aware date, number and currency
  formatting.
- Authentication: registration, sign-in, sign-out, password reset, email
  verification, refresh-token rotation and optional TOTP two-factor
  authentication.
- Role-based access control with protected administration routes.
- REST API with schema validation, consistent error envelopes and OpenAPI
  documentation at `/api-docs`.
- PostgreSQL persistence through Sequelize, with Redis-backed caching and
  background queues.
- Docker images for the API and the frontend, plus a Compose file wiring the
  application to PostgreSQL and Redis with health checks.
- Automated CI that installs, builds and boots the service, and a GitHub Pages
  workflow that publishes the live demo.

### Security
- Passwords hashed with bcrypt (cost factor 12).
- Helmet security headers, strict CORS, and rate limiting on all API routes.
- No default credentials; demo seeding requires an explicit opt-in and is
  always skipped when `NODE_ENV=production`.
