# Contributing to LumiCorePro

Thank you for your interest in contributing to LumiCorePro! Follow these guidelines to ensure smooth collaboration.

---

## 1. Development Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/your-org/lumicorepro-core.git
   cd lumicorepro-core
   ```

2. Install dependencies:
   ```bash
   npm install
   cd backend && npm install && cd ..
   ```

3. Start development environment:
   ```bash
   npm run dev:full
   ```
   - Frontend: `http://localhost:5173`
   - Backend: `http://localhost:5000`
   - Swagger Docs: `http://localhost:5000/api-docs`

---

## 2. Git & Branching Guidelines

- **Feature branches**: `feature/your-feature-name`
- **Bugfixes**: `fix/issue-description`
- **Documentation**: `docs/update-guide`

Commit messages should adhere to Conventional Commits:
```
feat(auth): add 2FA OTP verification endpoints
fix(ecommerce): resolve discount calculation on cart items
docs(api): update swagger spec for payments
```

---

## 3. Pull Request Checklist

Before submitting a PR:
- [ ] Run backend syntax validation: `node --check backend/server.js`
- [ ] Run test suite: `npm test`
- [ ] Verify production build: `npm run build`
- [ ] Format code: `npm run format`
- [ ] Ensure all new routes have Swagger JSDoc comments
