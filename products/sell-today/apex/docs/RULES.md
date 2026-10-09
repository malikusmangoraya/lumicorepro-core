# Project Engineering Rules & Standards — Apex

## 1. Code Integrity & Zero-Budget Standard

- **No Hardcoded Secrets**: Under no circumstances should private API keys (OpenAI, Stripe, database passwords) be committed. Use `.env.example` placeholders only.
- **Demo Mode Enforcement**: Every external integration (Payment, AI, Scraping) must provide a robust `mock_response()` fallback so the project works out of the box.
- **Client Activation Comments**: All integration points must be clearly marked:
  ```ts
  // CLIENT: Add the provider API key here to activate this feature.
  ```

## 2. Coding Standards

- 2-space indentation, consistent camelCase variables, and PascalCase components.
- Mobile-first Tailwind styling with accessible color contrast (WCAG 2.1 AA).
- All dependencies must be declared in `package.json` with strict semantic version ranges.
