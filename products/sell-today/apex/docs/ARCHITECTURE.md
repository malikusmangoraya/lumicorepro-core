# System Architecture — Apex

## 1. High-Level Architecture Overview

The application follows a decoupled, local-first full-stack architecture:

```
[ Client Browser ]
        │  (HTTPS / REST / WebSocket)
        ▼
[ Frontend: React 19 + Vite + Tailwind CSS ]
        │  (Axios API Client / Demo Fallback)
        ▼
[ Backend: Node.js + Express.js API Gateway ]
        │  (Prisma ORM / Parameterized Queries)
        ▼
[ Database: SQLite (Zero-Cost Local) / PostgreSQL ]
```

## 2. Frontend Layer (`frontend/` or `src/`)

- **Framework**: React 19 with Vite bundler.
- **Styling**: Tailwind CSS with design tokens defined in `src/themes/` and custom properties.
- **State Management**: Reactive hooks and modular context stores.
- **Mock Handlers**: All API endpoints fall back to `mock_response()` demo mode when backend or third-party keys are unconfigured.

## 3. Backend Layer (`backend/`)

- **Runtime**: Node.js 20+ with Express.js.
- **ORM / Database**: Prisma schema with SQLite as default zero-budget engine, easily switched to PostgreSQL.
- **Security**: CORS whitelist, helmet security headers, parameterized queries, and JWT authentication middleware.
