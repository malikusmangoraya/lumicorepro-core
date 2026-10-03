# 🛠️ GitHub & Lemon Squeezy Complete Workflow Guide

Yeh guide aap ke **LumicorePro AI Agent** aur is ke zariye banaye gaye projects ko **GitHub** aur **Lemon Squeezy** par manage aur sell karne ke liye mukammal manual hai.

---

## 1. Agent Repository Setup (GitHub)

Apne agent ke code ke liye GitHub par ek **Private Repository** banayein:

```bash
# 1. Initialize Git (agar pehle se initialized nahi hai)
git init

# 2. Files stage karein
git add .

# 3. Initial commit karein
git commit -m "feat: LumicorePro Master Prompt, 20 Design Styles & Zero-Budget architecture"

# 4. Main branch set karein
git branch -M main

# 5. Remote repository add karein (apna GitHub URL daalein)
git remote add origin https://github.com/YOUR_USERNAME/LumicorePro-Core.git

# 6. Push karein
git push -u origin main
```

---

## 2. Branching Strategy (Production Discipline)

- **`main` branch**: Hamesha 100% stable aur tested code.
- **`dev` branch**: Active development code jahan naye features integrate hotay hain.
- **`feature/` branches**: Har naye style ya engine ke liye alag branch (e.g. `feature/3d-experience`, `feature/glassmorphism-ui`).

### Workflow:
```bash
# Naya feature shuru karne ke liye:
git checkout -b feature/cyberpunk-preset

# Kaam karne ke baad commit aur push:
git add .
git commit -m "feat: add cyberpunk preset"
git push origin feature/cyberpunk-preset

# Dev branch mein merge karein aur test pass hone par main mein bhejein.
```

---

## 3. GitHub Actions (Free Automated CI/CD)

Aap ke repo mein 2000 minutes/month free GitHub Actions CI/CD setup hai:
1. **`.github/workflows/test.yml`**:
   - Har push aur PR par automatically chalta hai.
   - Code mein koi syntax error ya broken imports to nahi, check karta hai.
   - Design style catalog aur Python compilation verify karta hai.
2. **`.github/workflows/deploy.yml`**:
   - Client projects ko Cloudflare Pages ya GitHub Pages par automatically build aur deploy karta hai.

---

## 4. Free Deployment Architecture ($0/Month)

Aap ke agent ke generated projects **100% free hosting** par chalte hain:
- **Frontend**: **Cloudflare Pages** (Unlimited free bandwidth & edge SSL) ya **Netlify**.
  - `wrangler.toml` aur `netlify.toml` automatically project mein generate hotay hain.
- **Backend**: **Render (Free Tier)** ya **Fly.io**.
  - `render.yaml` aur `fly.toml` automatically shamil hotay hain.
- **Database**: **SQLite (Prisma)** local file storage. Zero database server fees!

---

## 5. Lemon Squeezy & Gumroad Selling Blueprint

Jab aap agent se koi project generate karein:

```bash
python ai-agent/main.py --prompt "Create an AI cyber art studio with digital canvas" --style cyberpunk
```

### Steps to Sell:
1. **Output Folder**: Project `ai-agent/generated-projects/<project-name>/` mein generate ho chuka hota hai.
2. **Verification**:
   - Folder mein `README.md`, `docs/PRD.md`, `docs/SETUP.md`, `docs/DEPLOYMENT.md`, aur `docs/COMPLIANCE.md` tayyar hain.
   - `.env.example` mein sirf placeholders hain (`OPENAI_API_KEY=YOUR_KEY_HERE`), koi private secret nahi.
   - AI aur Payments **Demo Mode** mein chalte hain baghair kisi paid API key ke.
3. **ZIP Archive**:
   - Project folder ka ZIP banayein (e.g. `cyber-art-studio-template.zip`).
4. **Lemon Squeezy Listing**:
   - Product type: **Digital Product**.
   - Price: **\$29 – \$79**.
   - Description mein `README.md` se Features aur Tech Stack copy karein.
   - Files section mein ZIP upload kar dein.

Jab buyer khareedega, wo ZIP extract kar ke `npm run dev` chalaye ga to website instantly chal paregi! Wo apni API keys `docs/SETUP.md` dekh kar `.env` mein khud daalega. Aap ka kharch **Zero** aur profit **100%**! 🚀
