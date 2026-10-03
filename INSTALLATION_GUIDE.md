# 📦 LumiCorePro Ultra - Installation & Setup Guide

> Complete step-by-step guide to install and configure all advanced features.

---

## 🎯 Quick Start (5 Minutes)

```bash
# 1. Clone repository
git clone https://github.com/your-username/lumicorepro-ultra.git
cd lumicorepro-ultra

# 2. Install dependencies
npm install
cd ai-agent && pip install -r requirements.txt && cd ..

# 3. Configure environment
cp .env.example .env
cp ai-agent/.env.example ai-agent/.env

# 4. Start everything
npm run dev:all
```

Access at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:5000
- AI Agent: http://localhost:8000

---

## 📋 Prerequisites

### Required
- **Node.js** 18+ ([Download](https://nodejs.org/))
- **Python** 3.10+ ([Download](https://python.org/))
- **PostgreSQL** 14+ ([Download](https://postgresql.org/))
- **Redis** 7+ ([Download](https://redis.io/))

### Optional (Recommended)
- **Docker** Desktop ([Download](https://docker.com/))
- **Git** ([Download](https://git-scm.com/))

---

## 🚀 Detailed Installation

### Step 1: System Dependencies

#### Windows
```powershell
# Using Chocolatey
choco install nodejs python postgresql redis git

# Or download installers manually
```

#### macOS
```bash
# Using Homebrew
brew install node python@3.10 postgresql redis git
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install nodejs npm python3.10 python3-pip postgresql redis-server git
```

---

### Step 2: Clone Repository

```bash
git clone https://github.com/your-username/lumicorepro-ultra.git
cd lumicorepro-ultra
```

---

### Step 3: Frontend Setup

```bash
# Install Node dependencies
npm install

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

#### Frontend Environment Variables (.env)

```env
# API Configuration
VITE_API_URL=http://localhost:5000
VITE_AI_API_URL=http://localhost:8000

# Feature Flags
VITE_ENABLE_ADVANCED_FEATURES=true
VITE_COMMAND_PALETTE_ENABLED=true
VITE_AI_CHAT_ENABLED=true

# AI Configuration
VITE_AI_DEFAULT_PROVIDER=gemini

# Analytics (Optional)
VITE_ANALYTICS_ENABLED=false
```

---

### Step 4: Backend Setup

```bash
cd backend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Edit .env
nano .env
```

#### Backend Environment Variables (backend/.env)

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/lumicorepro

# Redis
REDIS_URL=redis://localhost:6379

# JWT Secrets (CHANGE THESE!)
JWT_SECRET=your-super-secret-jwt-key-min-16-chars
JWT_REFRESH_SECRET=your-super-secret-refresh-key-min-16-chars

# Server
NODE_ENV=development
PORT=5000
FRONTEND_URL=http://localhost:5173

# AI Agent
AI_AGENT_URL=http://localhost:8000

# Email (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Payment Gateways (Optional)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
PAYPAL_CLIENT_ID=...
PAYPAL_CLIENT_SECRET=...
```

#### Initialize Database

```bash
# Create database
createdb lumicorepro

# Run migrations
npm run migrate

# Seed data (optional)
npm run seed
```

---

### Step 5: AI Agent Setup

```bash
cd ../ai-agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env
nano .env
```

#### AI Agent Environment Variables (ai-agent/.env)

```env
# AI Providers (Get API keys from respective platforms)
GEMINI_API_KEY=your-gemini-api-key
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
DEEPSEEK_API_KEY=your-deepseek-api-key
MISTRAL_API_KEY=your-mistral-api-key

# RAG Configuration
RAG_ENABLED=true
CHROMA_DB_PATH=./database/rag_store

# Code Intelligence
CODE_INTELLIGENCE_ENABLED=true

# Self-Healing
SELF_HEALING_ENABLED=true

# Multi-Modal
VISION_PROVIDER=gemini

# Server Configuration
AI_AGENT_HOST=0.0.0.0
AI_AGENT_PORT=8000

# Performance
AGENT_MAX_CONCURRENT_RUNS=2
AGENT_MAX_RUNS=100

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Optional: Rate Limiting
RATE_LIMIT_REQUESTS=30
RATE_LIMIT_WINDOW=60
```

#### Get AI API Keys

1. **Google Gemini**: [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
2. **OpenAI**: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
3. **Anthropic**: [https://console.anthropic.com/](https://console.anthropic.com/)
4. **DeepSeek**: [https://platform.deepseek.com/](https://platform.deepseek.com/)

#### Initialize AI Agent Database

```bash
python -c "from database.init_db import init_database; init_database()"
```

---

### Step 6: Install Advanced Dependencies

#### ChromaDB (for RAG)
```bash
cd ai-agent
pip install chromadb sentence-transformers
```

#### Code Analysis Tools
```bash
pip install radon bandit pylint black
```

#### Multi-Modal Support
```bash
pip install Pillow SpeechRecognition PyPDF2 python-docx openpyxl
```

#### Image Generation (Optional)
```bash
pip install stability-sdk replicate
```

---

## 🐳 Docker Setup (Alternative)

### Using Docker Compose

```bash
# Build and start all services
docker compose up --build -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Docker Environment

Create `docker-compose.override.yml` for local configuration:

```yaml
version: '3.8'

services:
  frontend:
    environment:
      - VITE_API_URL=http://localhost:5000
      - VITE_AI_API_URL=http://localhost:8000

  backend:
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/lumicorepro
      - REDIS_URL=redis://redis:6379

  ai-agent:
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - RAG_ENABLED=true
```

---

## 🧪 Verify Installation

### 1. Check Services

```bash
# Frontend
curl http://localhost:5173

# Backend API
curl http://localhost:5000/api/health

# AI Agent
curl http://localhost:8000/health
```

### 2. Test AI Generation

```bash
# Using curl
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Build a simple landing page",
    "provider": "gemini"
  }'
```

### 3. Run Tests

```bash
# Frontend tests
npm test

# Backend tests
cd backend && npm test

# AI Agent tests
cd ai-agent && python -m pytest
```

---

## 🎨 Advanced Feature Configuration

### Enable Command Palette

Already enabled by default! Press `Cmd+K` (Mac) or `Ctrl+K` (Windows/Linux).

### Enable RAG Engine

```env
# ai-agent/.env
RAG_ENABLED=true
```

Seed knowledge base:
```bash
cd ai-agent
python -c "from agent.rag_engine import get_rag_engine; rag = get_rag_engine(); rag.seed_best_practices()"
```

### Enable Code Intelligence

```env
# ai-agent/.env
CODE_INTELLIGENCE_ENABLED=true
```

### Enable Self-Healing

```env
# ai-agent/.env
SELF_HEALING_ENABLED=true
```

---

## 🔧 Troubleshooting

### Issue: Port Already in Use

```bash
# Find process using port
# Windows:
netstat -ano | findstr :5173
taskkill /PID <PID> /F

# macOS/Linux:
lsof -ti:5173 | xargs kill -9
```

### Issue: Database Connection Failed

```bash
# Check PostgreSQL status
# Windows:
Get-Service postgresql-x64-14

# macOS:
brew services list

# Linux:
sudo systemctl status postgresql

# Test connection
psql -U postgres -h localhost -d lumicorepro
```

### Issue: Redis Connection Failed

```bash
# Start Redis
# Windows:
redis-server

# macOS:
brew services start redis

# Linux:
sudo systemctl start redis

# Test connection
redis-cli ping
```

### Issue: Python Dependencies Failed

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install with verbose output
pip install -r requirements.txt -v

# Try with --no-cache-dir
pip install -r requirements.txt --no-cache-dir
```

### Issue: ChromaDB Installation Failed

```bash
# Install system dependencies first
# Ubuntu/Debian:
sudo apt install build-essential

# macOS:
xcode-select --install

# Then retry
pip install chromadb
```

### Issue: Node Modules Corrupted

```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
```

---

## 🚀 Production Deployment

### Environment Configuration

```env
# Frontend (.env.production)
VITE_API_URL=https://api.yourdomain.com
VITE_AI_API_URL=https://ai.yourdomain.com

# Backend (backend/.env.production)
NODE_ENV=production
DATABASE_URL=postgresql://user:password@prod-db:5432/lumicorepro
REDIS_URL=redis://prod-redis:6379
JWT_SECRET=<strong-random-secret-64-chars>

# AI Agent (ai-agent/.env.production)
AI_AGENT_HOST=0.0.0.0
AI_AGENT_PORT=8000
RAG_ENABLED=true
CODE_INTELLIGENCE_ENABLED=true
```

### Build for Production

```bash
# Frontend
npm run build

# Backend
cd backend && npm run build

# AI Agent (no build needed, just copy)
```

### Deploy to Vercel (Frontend)

```bash
npm install -g vercel
vercel --prod
```

### Deploy to Railway/Render (Backend + AI Agent)

1. Connect GitHub repository
2. Set environment variables
3. Deploy

---

## 📊 Performance Optimization

### 1. Enable Caching

```env
# Backend
REDIS_CACHE_ENABLED=true
CACHE_TTL=3600
```

### 2. CDN Configuration

Use Cloudflare or similar for static assets.

### 3. Database Optimization

```sql
-- Add indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_projects_user_id ON projects(user_id);
```

### 4. AI Agent Optimization

```env
# Limit concurrent runs
AGENT_MAX_CONCURRENT_RUNS=2

# Enable caching
RAG_CACHE_ENABLED=true
```

---

## 🔐 Security Checklist

- [ ] Change all default secrets
- [ ] Enable HTTPS in production
- [ ] Configure CORS properly
- [ ] Enable rate limiting
- [ ] Set up database backups
- [ ] Configure firewall rules
- [ ] Use environment-specific credentials
- [ ] Enable security headers
- [ ] Set up monitoring and alerts

---

## 📱 Mobile Development

### React Native Setup (Future)

```bash
# Install React Native CLI
npm install -g react-native-cli

# Create mobile app
npx react-native init LumiCoreProMobile
```

---

## 🎓 Next Steps

1. **Explore Features**: Open http://localhost:5173 and try the AI Dashboard
2. **Read Documentation**: Check [ADVANCED_FEATURES.md](./ADVANCED_FEATURES.md)
3. **Generate Your First Site**: Use Command Palette (Cmd+K) → "Generate New Website"
4. **Customize**: Modify components in `src/components/advanced/`
5. **Deploy**: Follow production deployment guide above

---

## 📞 Support & Resources

- 📖 **Documentation**: [ADVANCED_FEATURES.md](./ADVANCED_FEATURES.md)
- 🚀 **Upgrade Guide**: [UPGRADE_ROADMAP.md](./UPGRADE_ROADMAP.md)
- 💬 **Discord**: [Join Community](https://discord.gg/your-server)
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- 📧 **Email**: support@lumicorepro.com

---

## 🎉 You're All Set!

LumiCorePro Ultra is now installed and ready to use. Start generating amazing websites with AI! 🚀

---

**Happy Coding! 💻✨**

Last Updated: 2026-09-19  
Version: 2.0.0-ultra
