# LumicorePro Core 🚀

**AI-Powered Full-Stack Website Generator** — Build production-ready websites from a single natural language prompt.

LumicorePro Core is a modular React-based component library combined with a **9-phase AI agent pipeline** that automatically generates complete full-stack projects (React + Vite + Tailwind + Node.js + Express + PostgreSQL) tailored to **market demand and trending features**.

> **One prompt. Complete website. Market-optimized. Ready to deploy.**
>
> **Enhanced v2.0** — More industries, robust pipeline, better AI integration, improved error recovery, and comprehensive component library.

## ✨ Features

- **React 19** with Vite for fast development
- **Tailwind CSS** for utility-first styling with premium glassmorphism theme
- **React Router DOM** for client-side routing
- **Dark/Light mode** with system preference detection
- **Axios** for API communication
- **Lucide React** icons
- **Framer Motion** for smooth animations
- **Recharts** for interactive data visualization
- **Responsive design** (mobile-first)
- **Context API** for global state management
- **10+ Industry Website Templates** (E-commerce, SaaS, Healthcare, Education, Fitness, etc.)
- **100+ Reusable Components** across all categories
- **9-Phase AI Generation Pipeline** with market analysis
- **Multi-AI Provider Support** (Gemini, DeepSeek, OpenRouter) with fallback chain
- **Market Demand Analysis** — auto-injects trending features based on industry
- **Competitive Benchmarking** — ROI scoring & industry comparison
- **Quality Gates** — automated code quality evaluation
- **Offline Mode** — works without AI API keys using local rules
- **Enhanced Requirement Analysis** — supports 20+ industries (fintech, social media, fashion, electronics, automotive, legal, nonprofit, government, agriculture)
- **Robust Pipeline** — per-phase error handling, recovery, and comprehensive logging
- **AI-Driven Code Generation** — full component generation with security scanning
- **Auto NPM Dependency Fixing** — detects missing packages and injects them automatically
- **Design System Injection** — premium glassmorphism theme with Tailwind config
- **Interactive Setup Wizard** — guided environment configuration
- **Comprehensive Test Suite** — unit tests for all agent modules

## 🌐 Supported Website Types

| Industry | Category | Features |
|----------|----------|----------|
| **E-Commerce** | Electronics, Fashion, Retail | Products, Cart, Checkout, Payments, Reviews |
| **SaaS** | Software, Analytics | Dashboards, Pricing, Plans, Metrics |
| **Business** | Corporate, Agency, Landing | Services, Portfolio, Team, Testimonials |
| **Healthcare** | Medical, Clinic, Hospital | Appointments, Patient Portal, Doctor Profiles |
| **Education** | LMS, Course Platform | Courses, Lessons, Progress Tracking |
| **Food & Dining** | Restaurant, Cafe, Delivery | Menu, Online Ordering, Delivery Tracking |
| **Fitness** | Gym, Training, Wellness | Classes, Scheduling, Membership Plans |
| **Real Estate** | Property, Rentals | Listings, Search, Maps, Agent Profiles |
| **Travel** | Agency, Tours, Vacation | Destinations, Booking, Itineraries |
| **Portfolio** | Personal, Creative, Freelance | Projects, Skills, Contact Forms |
| **Fintech** | Crypto, Trading, Banking | Wallet, Charts, Transactions, Security |
| **Social Media** | Community, Networking | Profiles, Posts, Feed, Messaging |
| **Automotive** | Cars, Dealerships | Vehicles, Test Drives, Financing |
| **Non-Profit** | Charity, NGO | Donations, Events, Impact Stories |
| **Job Board** | Recruitment, Careers | Job Listings, Applications, Employer Profiles |

## 🤖 AI Agent Pipeline (9 Phases)

The AI agent transforms any natural language prompt into a complete full-stack project through **9 sequential phases**:

```
Prompt ─→ [1] Market Analysis ─→ Industry demand, competition, positioning
          [2] Requirement Analysis ─→ AI + rule-based parsing, ambiguity detection
          [3] Tech Stack Selection ─→ Frontend, Backend, Database matching
          [4] Trending Features ─→ Auto-inject high-ROI market features
          [5] Resource Assembly ─→ Template + Components + Assets + Backend
          [6] Code Generation ─→ Project build, AI customization, NPM fix
          [7] Quality Gates ─→ Structure validation, completeness scoring
          [8] Improvements ─→ Missing features, enhancements, recommendations
          [9] Competitive Benchmark ─→ ROI scoring, market comparison, ZIP delivery
          ─→ Complete Full-Stack Project (ZIP + Deployment Guide)
```

### How Each Phase Works

| Phase | Agent | Description | Fallback |
|-------|-------|-------------|----------|
| **1. Market Analysis** | `MarketAnalyzer` | Analyzes industry demand, competition, and customer segments | Static industry scoring |
| **2. Requirement Analysis** | `RequirementAnalyzer` | Parses prompt, detects ambiguity, infers implicit features | Local keyword rules |
| **3. Tech Stack** | `TechStackSelector` | Selects optimal frontend/backend/database stack | React + Express + PostgreSQL |
| **4. Trending Features** | `TrendingFeaturesInjector` | Injects high-ROI features (social proof, AI chat, smart search) | Skips if no match |
| **5. Resource Assembly** | `GenerationPlanner` | Plans template, components, assets, backend, database | Default template |
| **6. Code Generation** | `ProjectBuilder` | Copies resources, fixes dependencies, injects design system | Minimal scaffold |
| **7. Quality Verification** | `ProjectValidator` | Validates project structure, files, dependencies | Returns basic report |
| **8. Improvements** | `ImprovementRecommender` | Recommends features, performance, security improvements | Static suggestions |
| **9. Competitive Benchmark** | `CompetitiveBenchmark` | Market comparison, ROI score, delivery package | Basic benchmark |

> **No internet? No problem.** All phases have offline local fallbacks.

## 📁 Project Structure

```
lumicorepro-core/
├── src/                          # Frontend source
│   ├── components/               # 100+ reusable React components
│   │   ├── ui/                   # Buttons, Cards, Modals, etc.
│   │   ├── common/               # Theme, Language, Layout helpers
│   │   ├── navigation/           # Navbar, Footer, Sidebar, Breadcrumb
│   │   ├── forms/                # Input, Select, Checkbox, etc.
│   │   ├── ecommerce/            # ProductCard, Cart, Checkout
│   │   ├── dashboard/            # Charts, DataTable, StatCards
│   │   ├── ai/                   # ChatBox, ChatInput, MessageList
│   │   ├── business/             # Hero, FeatureGrid, PricingCard
│   │   ├── auth/                 # LoginForm, RegisterForm, OTP
│   │   ├── layout/               # Page layout wrappers
│   │   └── editor/               # Visual page editor
│   ├── context/                  # React Context providers
│   ├── hooks/                    # Custom React hooks
│   ├── layouts/                  # Page layout templates
│   ├── pages/                    # Route page components
│   ├── routes/                   # Router configuration
│   ├── services/                 # API communication layer
│   ├── styles/                   # Global CSS & animations
│   ├── templates/                # 10 industry website templates
│   │   ├── business/             # Corporate template
│   │   ├── ecommerce/            # Electronics templates (3 variants)
│   │   ├── education/            # LMS template
│   │   ├── fitness/              # Gym template
│   │   ├── healthcare/           # Medical template
│   │   ├── portfolio/            # Personal portfolio template
│   │   ├── realestate/           # Property template
│   │   ├── restaurant/           # Cafe template
│   │   ├── travel/               # Agency template
│   │   └── creative/             # Studio template
│   └── icons/                    # SVG icon assets
├── ai-agent/                     # AI generation engine
│   ├── agent/                    # 15+ specialized agent modules
│   ├── config/                   # Settings & provider config
│   ├── database/                 # Agent memory database
│   ├── providers/                # AI provider implementations
│   └── utils/                    # Helpers, Logger, FileManager
├── backend/                      # Express.js API
├── backend-library/              # 4 backend base templates
│   ├── ecommerce-base/           # E-commerce API
│   ├── electronics-backend/      # Electronics API
│   ├── saas-backend/             # SaaS API
│   └── master-express-backend/   # Business/Contact API
├── database/                     # Schema management
│   └── schemas/                  # PostgreSQL schema files
├── registry/                     # Local asset library
│   ├── templates.json            # Template registry (10 templates)
│   ├── components.json           # Component registry (40+ components)
│   ├── backend-modules.json      # Backend base registry (4 backends)
│   ├── images.json               # Image asset registry (20+ images)
│   ├── icons.json                # Icon asset registry (14 icons)
│   ├── animations.json           # Animation CSS registry (10 animations)
│   └── trending-features.json    # Market trending features (7 features)
├── generated-projects/           # AI-generated output directory
├── project-rules/                # Development standards
├── docs/                         # Documentation
└── public/                       # Static assets
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- npm 9+
- Python 3.9+ (for AI agent)

### Installation (Frontend)

```bash
# Clone the repository
git clone <repo-url>
cd lumicorepro-core

# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Start development server
npm run dev
```

### Installation (AI Agent)

```bash
# Setup Python environment
cd ai-agent
pip install -r requirements.txt

# Initialize agent database
python database/init_db.py

# Configure AI provider (copy .env.example to .env)
cp .env.example .env
# Edit .env with your API keys
```

## AI Agent Usage

### Generate a Project

```bash
cd ai-agent

# Basic usage
python main.py --prompt "Build me a premium electronics e-commerce store"

# Interactive mode (asks for clarification if needed)
python main.py --prompt "Build me a website" --interactive

# Specify AI provider
python main.py --prompt "SaaS dashboard with analytics" --provider gemini
```

### AI Provider Configuration

Edit `ai-agent/.env`:

```env
# Choose provider: gemini | deepseek | openrouter
AI_PROVIDER=gemini

# Set your API key
GEMINI_API_KEY=your_api_key_here

# Model selection
GEMINI_MODEL=gemini-2.5-flash
```

### Output

Generated projects are saved in `generated-projects/` with:
- **Frontend** (React + Vite + Tailwind)
- **Backend** (Node.js + Express)
- **Database** (PostgreSQL schema)
- **INSTRUCTIONS.md** (step-by-step deployment guide)
- **ZIP archive** (ready for deployment)

The generated project receives:
1. A **quality score** (0-100%) evaluating structure completeness
2. **Improvement recommendations** (missing features, performance tips)
3. A **competitive benchmark report** with ROI scoring
4. A **deployment guide** (INSTRUCTIONS.md) with setup, DB migration, and cloud deployment steps

## 🔧 Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |

## ⚙️ Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API endpoint | `http://localhost:3001` |
| `VITE_ENV` | Environment mode | `development` |
| `VITE_ENABLE_MOCK_API` | Enable mock data | `true` |
| `VITE_ENABLE_DARK_MODE` | Default dark mode | `true` |

## 📚 Documentation

### AI Agent System (Start Here)
- [Quick Reference](docs/LUMICOREPRO_QUICK_REFERENCE.md) — Complete system overview
- [Master Agent Prompt v3](docs/MASTER_AGENT_PROMPT_v3.md) — 9-phase AI generation
- [Implementation Guide](docs/MASTER_AGENT_IMPLEMENTATION.md) — Integration architecture
- [Executive Summary](docs/LUMICOREPRO_EXECUTIVE_SUMMARY.md) — 4-week launch plan
- [System Prompt](docs/LUMICOREPRO_SYSTEM_PROMPT.md) — Quality standards
- [Improvements Roadmap](docs/LUMICOREPRO_IMPROVEMENTS_ROADMAP.md) — Feature priorities

### Architecture
- [Phase 1 Guide](docs/PHASE_1_GUIDE.md) — Setup and installation
- [Project Rules](project-rules/PROJECT_RULES.md) — Code standards
- [Architecture](project-rules/ARCHITECTURE.md) — System design

## 🏗️ Component Library

### UI Components (26)
Button, Card, Modal, Alert, Tabs, Dropdown, Progress, Spinner, Tooltip, Badge, Avatar, Breadcrumb, Pagination, Skeleton, Loading, Empty, Divider, IconButton, Accordion

### E-Commerce Components (22)
ProductCard, ProductGrid, ProductDetails, ProductImage, CartItem, CartSummary, CartEmpty, AddToCart, AddToWishlist, Checkout, OrderConfirmation, SearchProducts, CategoryFilter, PriceFilter, SortOptions, DiscountBadge, RatingStars, ReviewForm, QuantitySelector, ShippingInfo, ProductList, ProductReview

### Dashboard Components (20)
DashboardLayout, DashboardHeader, DashboardSidebar, StatCard, RevenueCard, PerformanceCard, AreaChart, BarChart, LineChart, PieChart, ChartCard, DataTable, DateRangeFilter, SearchBar, RecentOrders, ActivityFeed, FilterPanel, ExportButton, NotificationBell, UserProfile

### Business Components (14)
Hero, FeatureGrid, PricingCard, PricingGrid, Testimonial, TestimonialSlider, FAQItem, CTA, Team, TeamGrid, ServiceCard, Feature, PortfolioGrid, PortfolioItem

### Auth Components (8)
LoginForm, RegisterForm, ForgotPassword, ResetPassword, OTPInput, SocialLogin, AuthWrapper, ProtectedRoute

### Navigation Components (9)
Navbar, Footer, Sidebar, MobileMenu, Breadcrumb, TabNavigation, Stepper, TopMenu, VerticalMenu

### AI Components (12)
ChatBox, ChatInput, ChatMessage, MessageList, ModelSelector, TokenCounter, TypingIndicator, CopyButton, RegenerateButton, GenerationCard, HistoryPanel, PromptTemplates, UploadFile, AIResponse

### Form Components (13)
Input, Select, Textarea, Checkbox, Radio, Switch, DatePicker, TimePicker, RangeSlider, Rating, SearchInput, FileUpload, FormError, FormGroup

### Layout Components (4)
MainLayout, DashboardLayout, AuthLayout, BlogLayout

## Security

- Path traversal protection in all file operations
- Code security scanning (blocks eval, exec, dangerous patterns)
- Balanced syntax validation for generated code
- AI response security audit before applying

## 📊 AI Agent Architecture

```
┌─────────────────────────────────────────────────────┐
│                  AgentOrchestrator                   │
│              (Master 9-Phase Pipeline)               │
├────────────┬────────────┬────────────┬──────────────┤
│ Phase 1-2  │ Phase 3-4  │ Phase 5    │ Phase 6      │
│ Market +   │ Tech Stack │ Resource   │ Code         │
│ Req Analysis│ Selection │ Assembly   │ Generation   │
├────────────�────────────┴────────────┴──────────────┤
│ Phase 7-9                                           │
│ Quality Gates + Improvements + Competitive          │
│ Benchmark + Delivery                                │
└─────────────────────────────────────────────────────┘
         │              │              │
  ┌──────┴───┐  ┌──────┴───┐  ┌──────┴───┐
  │AI Provider│  │Registry  │  │Local     │
  │(Gemini/  │  │(Templates│  │Library   │
  │DeepSeek) │  │ /Comp.)  │  │(Images / │
  │           │  │          │  │ Icons)   │
  └──────────┘  └──────────┘  └──────────┘
```

## 📦 Local Library

| Resource | Count | Description |
|----------|-------|-------------|
| Templates | 10 | Industry-specific website templates |
| Components | 100+ | Reusable React components |
| Backend Bases | 4 | Express.js API templates |
| DB Schemas | 10+ | PostgreSQL schema files |
| Images | 20+ | HD product/hero images |
| Icons | 14 | SVG icon assets (smartphone, laptop, headphones, smartwatch, TV, camera, speaker, gamepad, cart, heart, user, search, shield, truck) |
| Animations | 10 | CSS animation classes (glow pulse, hover float, shimmer, glass fade, border rotate, bounce, ripple, gradient shift, cart bounce, particle float) |

### Supported Industries

| Industry | Description | Templates |
|----------|-------------|-----------|
| **Electronics E-Commerce** | Gadgets, smartphones, computers, accessories | Electronics Template 01/02/03 |
| **Fashion** | Clothing, footwear, accessories | (upcoming) |
| **SaaS/Business** | Enterprise dashboards, subscription platforms | SaaS Template, Corporate Template |
| **Healthcare** | Medical clinics, patient portals, telemedicine | Medical Template |
| **Education (LMS)** | Online courses, learning management | LMS Template |
| **Fitness** | Gym, workout, personal trainer | Gym Template |
| **Travel** | Tourism, booking, destinations | Agency Template |
| **Real Estate** | Property listings, estate agencies | Property Template |
| **Restaurant** | Café, food delivery, menus | Café Template |
| **Portfolio** | Personal brand, resume, creative | Personal Portfolio Template |
| **Creative/Agency** | Design agency, photography, art | Studio Template |
| **Fintech** | Trading platforms, crypto, banking | (upcoming) |

## � License

MIT

---

## ❓ FAQ

**Q: Does the AI agent work without an internet connection?**  
Yes! The agent has full offline fallback. All 9 phases can run using local rule-based analysis without any AI API keys. The quality is slightly higher with a provider connected, but the system remains fully functional offline.

**Q: Which AI provider is recommended?**  
Google Gemini (gemini-2.5-flash) provides the best balance of speed and quality. DeepSeek and OpenRouter are excellent alternatives if you prefer them.

**Q: How long does project generation take?**  
With AI provider: 30-90 seconds depending on prompt complexity.  
Without AI provider (offline): 5-15 seconds.

**Q: Can I customize the generated project?**  
Absolutely! Every generated project is standard React + Vite + Express code. Open it in your IDE and modify freely. Each project includes a step-by-step `INSTRUCTIONS.md` deployment guide.

**Q: What happens if the AI provider is down?**  
The system automatically falls back through the provider chain (e.g., Gemini → DeepSeek → OpenRouter → Local). If all providers fail, it continues with local rule-based analysis.

**Q: Can I add my own templates or components?**  
Yes! Place templates in `src/templates/your-industry/` and register them in `registry/templates.json`. Similarly, add components to `src/components/` and `registry/components.json`.

**Q: How do I run the generated project?**  
Each generated project includes `INSTRUCTIONS.md` with step-by-step setup. In short:
```bash
cd frontend && npm install && npm run dev   # Frontend
cd backend  && npm install && npm run dev   # Backend
psql -U postgres -d lumicore_db -f database/schema.sql   # Database
```

**Q: What databases are supported?**  
PostgreSQL is the primary supported database. The agent generates consolidated SQL schema files ready to run on PostgreSQL 14+.

---

## 🐛 Troubleshooting

### "Failed to load template" Error

**Cause:** Template path mismatch between registry and filesystem.  
**Fix:** Ensure `registry/templates.json` `file_path` values match actual directories under `src/templates/`. The agent will auto-fallback to the corporate template if no match is found.

### "pip install -r requirements.txt" fails

**Cause:** Missing Python or pip not installed.  
**Fix:** Install Python 3.9+ from [python.org](https://python.org), then run:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### "AI provider initialization failed"

**Cause:** Invalid or missing API key.  
**Fix:** Check `ai-agent/.env` has the correct API key for your chosen provider. The system will fallback to offline mode automatically.

### "Template path not found" Warning

**Cause:** The template specified in the registry doesn't exist on disk.  
**Fix:** The agent auto-falls back to the corporate template. To add custom templates, place them in `src/templates/` and update `registry/templates.json`.

### "Port already in use" Error

**Cause:** Another process is using port 5173 (frontend) or 5000 (backend).  
**Fix:** Run `lsof -i :5173` (Mac/Linux) or `netstat -ano | findstr :5173` (Windows) to find and kill the process.

### Generated project is missing features

**Cause:** The prompt was too vague or the feature wasn't in the registry.  
**Fix:** Use more specific prompts like "Build an electronics e-commerce store with product filters, cart, checkout, customer reviews, and wishlist" to get better results. You can also run in `--interactive` mode for guided clarification.

### "Module not found" errors in generated frontend

**Cause:** Missing NPM dependencies.  
**Fix:** The agent auto-fixes dependencies in Phase 6. If issues persist, run:
```bash
cd generated-projects/your-project/frontend
npm install --force
npm run dev
```
