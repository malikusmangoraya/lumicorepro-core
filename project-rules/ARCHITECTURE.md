# Architecture - LumicorePro Core

## Tech Stack
- **Frontend:** React 19 + Vite
- **Styling:** Tailwind CSS
- **Routing:** React Router DOM
- **HTTP Client:** Axios
- **Icons:** Lucide React
- **State Management:** React Context API

## Project Structure

```
lumicorepro-core/
├── src/
│   ├── components/       # Reusable UI components
│   │   ├── ui/           # Basic UI elements
│   │   ├── common/       # Shared components
│   │   ├── navigation/   # Navigation components
│   │   ├── forms/        # Form components
│   │   ├── ecommerce/    # E-commerce specific
│   │   ├── dashboard/    # Dashboard widgets
│   │   ├── ai/           # AI-related components
│   │   ├── business/     # Business logic UI
│   │   └── auth/         # Authentication UI
│   ├── icons/            # Icon exports by category
│   ├── assets/           # Images, fonts, logos
│   ├── pages/            # Page components
│   ├── layouts/          # Layout wrappers
│   ├── hooks/            # Custom React hooks
│   ├── services/         # API client & endpoints
│   ├── utils/            # Helper functions
│   ├── data/             # Static data & constants
│   ├── routes/           # React Router configuration
│   ├── styles/           # Global CSS & design system
│   └── context/          # React Context providers
├── project-rules/        # Development rules & standards
├── docs/                 # Documentation
├── backend/              # Backend API (future)
├── database/             # Database schema (future)
├── ai-agent/             # AI agent integration (future)
└── templates/            # Project templates (future)
```

## Architecture Principles

### Component Architecture
- **Pages** → high-level route components
- **Layouts** → wrap pages with common UI (navbar, footer)
- **Components** → reusable, self-contained UI pieces
- **Hooks** → custom logic extraction
- **Services** → API communication layer

### State Management
- **Local State:** `useState` for component-level state
- **Global State:** Context API for theme, auth, notifications
- **URL State:** React Router for navigation state

### API Layer
- Centralized Axios instance in `src/services/api.js`
- Request/response interceptors for auth tokens
- Environment-based API URL configuration
- Error handling with user-friendly messages

### Styling
- Tailwind CSS for utility-first styling
- Design system variables in `globals.css`
- Dark mode via CSS variables + class toggle
- Responsive breakpoints: sm, md, lg, xl, 2xl

## Data Flow
```
User Action → Component → Hook/Service → API → Response → State Update → Re-render
```

## Environment Variables
All prefixed with `VITE_` for Vite compatibility:
- `VITE_API_URL` - Backend API endpoint
- `VITE_ENV` - Development/Production
- `VITE_ENABLE_MOCK_API` - Toggle mock data
- `VITE_ENABLE_DARK_MODE` - Default theme