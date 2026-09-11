# Project Rules - LumicorePro Core

## Code Style
- Use functional components with hooks
- Use JSX syntax
- Follow ESLint + Prettier configuration
- 2-space indentation
- Single quotes for strings
- Semicolons required
- Max line length: 100 characters

## Naming Conventions
- Components: PascalCase (`MainLayout.jsx`)
- Utilities: camelCase (`helpers.js`)
- Hooks: camelCase with `use` prefix (`useWindowSize.js`)
- Constants: UPPER_SNAKE_CASE
- Files: match component name (PascalCase for components, camelCase for utilities)

## File Organization
- One component per file
- Export default for main components
- Named exports for utilities
- Keep files under 300 lines

## React Patterns
- Use React Router for navigation
- Use Context API for global state
- Use Axios for API calls
- Implement error boundaries
- Use `useEffect` cleanup for subscriptions

## Tailwind CSS
- Use Tailwind utility classes
- Custom styles in `globals.css`
- Responsive design first
- Dark mode support required

## Git Workflow
- Feature branches for new work
- Commit messages: "Type: description" (e.g., "feat: add home page")
- Keep commits small and focused
- Always pull before pushing

## Testing
- Write tests for utilities
- Test critical user flows
- Aim for 80%+ coverage

## Security
- Never commit `.env` files
- Validate all user input
- Use environment variables for secrets
- Sanitize API responses
