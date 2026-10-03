# ✅ LumiCorePro Ultra - Quick Start Checklist

> Follow this step-by-step checklist to get up and running in 10 minutes.

---

## 📋 Pre-Installation Checklist

Before you begin, make sure you have:

- [ ] **Node.js 18+** installed ([Download](https://nodejs.org/))
- [ ] **Python 3.10+** installed ([Download](https://python.org/))
- [ ] **PostgreSQL 14+** installed ([Download](https://postgresql.org/))
- [ ] **Redis 7+** installed ([Download](https://redis.io/))
- [ ] **Git** installed ([Download](https://git-scm.com/))

---

## 🚀 Installation Steps

### Step 1: Clone Repository ✅
```bash
git clone https://github.com/your-username/lumicorepro-ultra.git
cd lumicorepro-ultra
```

**Verification**: `ls` should show package.json, README.md, etc.

---

### Step 2: Install Frontend Dependencies ✅
```bash
npm install
```

**Verification**: `node_modules/` folder created, no errors in terminal

---

### Step 3: Install Backend Dependencies ✅
```bash
cd backend
npm install
cd ..
```

**Verification**: `backend/node_modules/` folder created

---

### Step 4: Install AI Agent Dependencies ✅
```bash
cd ai-agent

# Create virtual environment
python -m venv venv

# Activate it
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt

cd ..
```

**Verification**: `(venv)` prefix in terminal, no pip errors

---

### Step 5: Configure Environment Variables ✅

#### Frontend (.env)
```bash
cp .env.example .env
```

Edit `.env` and set:
```env
VITE_API_URL=http://localhost:5000
VITE_AI_API_URL=http://localhost:8000
VITE_ENABLE_ADVANCED_FEATURES=true
```

#### Backend (backend/.env)
```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and set:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/lumicorepro
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-super-secret-jwt-key-change-this
JWT_REFRESH_SECRET=your-super-secret-refresh-key-change-this
```

#### AI Agent (ai-agent/.env)
```bash
cp ai-agent/.env.example ai-agent/.env
```

Edit `ai-agent/.env` and set:
```env
# Get free API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your-gemini-api-key-here

# Enable advanced features
RAG_ENABLED=true
CODE_INTELLIGENCE_ENABLED=true
SELF_HEALING_ENABLED=true
```

**Verification**: All 3 `.env` files exist and contain your keys

---

### Step 6: Setup Database ✅
```bash
# Create database
createdb lumicorepro

# Or using psql:
psql -U postgres -c "CREATE DATABASE lumicorepro;"

# Initialize AI Agent database
cd ai-agent
python -c "from database.init_db import init_database; init_database()"
cd ..
```

**Verification**: Database created, no errors

---

### Step 7: Start Services ✅

Open **3 separate terminals**:

#### Terminal 1: Frontend
```bash
npm run dev
```
**Expected**: `Local: http://localhost:5173`

#### Terminal 2: Backend
```bash
cd backend
npm run dev
```
**Expected**: `Server running on http://localhost:5000`

#### Terminal 3: AI Agent
```bash
cd ai-agent
# Activate venv first (Windows: .\venv\Scripts\Activate.ps1)
python server.py
```
**Expected**: `Uvicorn running on http://0.0.0.0:8000`

---

## 🧪 Verification Tests

### Test 1: Frontend ✅
Open browser: http://localhost:5173

**Expected**: Homepage loads with navigation

---

### Test 2: Backend API ✅
```bash
curl http://localhost:5000/api/health
```

**Expected**: `{"success":true,"status":"healthy"}`

---

### Test 3: AI Agent ✅
```bash
curl http://localhost:8000/health
```

**Expected**: `{"status":"healthy"}`

---

### Test 4: Command Palette ✅
In browser (http://localhost:5173):
1. Press `Cmd+K` (Mac) or `Ctrl+K` (Windows/Linux)
2. Command palette should open

**Expected**: Modal with search input appears

---

### Test 5: AI Dashboard ✅
Navigate to: http://localhost:5173/ai-dashboard

**Expected**: Dashboard with animated background and stats cards

---

### Test 6: Generate Website (The Big Test!) ✅
1. Go to AI Dashboard: http://localhost:5173/ai-dashboard
2. Type in prompt: "Build a simple landing page"
3. Click "Generate Website"
4. Watch the logs stream

**Expected**:
- WebSocket connects
- Progress bar animates 0% → 100%
- Logs show phase completions
- Success message appears

---

## 🎨 Explore Features

Now that everything works, try these:

### 1. Premium Components ✅
Create a new page with GlassCard:
```jsx
import GlassCard from '@/components/advanced/GlassCard';

function MyPage() {
  return (
    <GlassCard intensity="high" tiltEffect={true}>
      <h1>Hello Ultra!</h1>
      <p>Move your mouse to see the 3D tilt effect!</p>
    </GlassCard>
  );
}
```

---

### 2. Code Intelligence ✅
Analyze a project:
```bash
cd ai-agent
python -c "
from agent.code_intelligence import get_code_intelligence
from pathlib import Path

ci = get_code_intelligence()
metrics = ci.analyze_project(Path('../generated-projects/test-site'))
print(f'Security Score: {metrics.security_score}/100')
print(f'Issues: {len(metrics.issues)}')
"
```

---

### 3. RAG Engine ✅
Seed knowledge base:
```bash
cd ai-agent
python -c "
from agent.rag_engine import get_rag_engine

rag = get_rag_engine()
rag.seed_best_practices()
print('Knowledge base seeded!')
"
```

---

### 4. Multi-Modal ✅
Process a screenshot:
```bash
cd ai-agent
python -c "
from agent.multimodal_processor import get_multimodal_processor

processor = get_multimodal_processor()
# Process your screenshot here
print('Multi-modal processor ready!')
"
```

---

## 🐛 Troubleshooting

### Issue: Port already in use

**Solution**:
```bash
# Windows:
netstat -ano | findstr :5173
taskkill /PID <PID> /F

# macOS/Linux:
lsof -ti:5173 | xargs kill -9
```

---

### Issue: Database connection failed

**Solution**:
1. Check if PostgreSQL is running
2. Verify DATABASE_URL in backend/.env
3. Try: `psql -U postgres -d lumicorepro` to test connection

---

### Issue: Python dependencies failed

**Solution**:
```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Try installing with verbose output
pip install -r requirements.txt -v
```

---

### Issue: ChromaDB won't install

**Solution**:
```bash
# Install build tools first
# macOS:
xcode-select --install

# Windows:
# Download Visual C++ Build Tools

# Then retry:
pip install chromadb
```

---

### Issue: Command Palette doesn't open

**Solution**:
1. Check browser console for errors
2. Verify CommandPalette is imported in App.jsx
3. Try refreshing page (Ctrl+R)

---

## 📚 Next Steps

Once everything is working:

1. **Read Documentation**:
   - [ ] [Advanced Features Guide](./ADVANCED_FEATURES.md)
   - [ ] [Installation Guide](./INSTALLATION_GUIDE.md)
   - [ ] [What's New](./WHATS_NEW.md)

2. **Try Advanced Features**:
   - [ ] Generate a real website
   - [ ] Run code intelligence on it
   - [ ] Use self-healing to fix any errors
   - [ ] Explore premium components

3. **Customize**:
   - [ ] Modify components in `src/components/advanced/`
   - [ ] Add your own RAG knowledge
   - [ ] Create custom AI commands
   - [ ] Build your own theme

4. **Deploy** (Optional):
   - [ ] Build for production: `npm run build`
   - [ ] Deploy frontend to Vercel
   - [ ] Deploy backend to Railway
   - [ ] Configure domain and SSL

---

## 🎉 You're Ready!

Congratulations! Your LumiCorePro Ultra installation is complete.

**Key Shortcuts**:
- `Cmd+K` / `Ctrl+K` - Command Palette
- `/ai-dashboard` - AI Control Center
- `Shift+Enter` - New line in AI chat

**Useful Commands**:
```bash
npm run dev          # Frontend
npm run build        # Production build
npm run test         # Run tests
npm run lint         # Check code quality
```

---

## 💡 Pro Tips

1. **Use Command Palette** for everything - it's faster than clicking
2. **Enable RAG** for better AI generations
3. **Run Code Intelligence** after every generation
4. **Use Self-Healing** to catch errors early
5. **Explore Components** in Storybook (if installed)

---

## 📞 Need Help?

- 📖 [Read the Docs](./ADVANCED_FEATURES.md)
- 🐛 [Report Issues](https://github.com/your-repo/issues)
- 💬 [Join Discord](https://discord.gg/your-server)
- 📧 Email: support@lumicorepro.com

---

**Happy Building! 🚀✨**

Estimated Time to Complete: **10-15 minutes**  
Difficulty: **Beginner Friendly**  
Support: **24/7 Documentation + Community**

---

Last Updated: 2026-09-19  
Version: 2.0.0-ultra
