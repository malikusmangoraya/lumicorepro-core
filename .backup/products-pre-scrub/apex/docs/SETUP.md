# Client Setup & API Key Configuration Guide

Welcome to your new **Apex** application! This project is 100% functional out of the box in **Demo Mode**. To activate live third-party services (AI, Payments, Database), follow this step-by-step guide.

---

## 1. Local Development Quickstart

### Prerequisites

- Node.js (v18 or v20+)
- npm or pnpm or yarn

### Installation

```bash
# 1. Install frontend dependencies
cd frontend
npm install

# 2. Install backend dependencies
cd ../backend
npm install
```

### Running the App

```bash
# In frontend directory:
npm run dev

# In backend directory (in another terminal):
npm run dev
```

Open `http://localhost:5173` to view the live app!

---

## 2. API Key Configuration

To connect real services, copy `.env.example` to `.env` in both `frontend` and `backend`:

```bash
cp .env.example .env
```

### A. Stripe Payment Gateway (Optional)

1. Sign up at [https://stripe.com](https://stripe.com).
2. Go to **Developers ➔ API Keys**.
3. Copy your **Publishable Key** into `VITE_STRIPE_PUBLISHABLE_KEY` in frontend `.env`.
4. Copy your **Secret Key** into `STRIPE_SECRET_KEY` in backend `.env`.

> In Demo Mode, payments simulate instant success without charging any card!

### B. OpenAI / LLM API Key (Optional)

1. Sign up at [https://platform.openai.com](https://platform.openai.com).
2. Navigate to **API Keys** and click **Create new secret key**.
3. Place your key in `backend/.env`:
   ```env
   OPENAI_API_KEY=sk-...
   ```

> In Demo Mode, the app uses built-in smart mock responses (`mock_response()`) without consuming any tokens.

### C. Database Connection

- By default, the application runs on **SQLite** (`file:./dev.db`), which requires zero setup and zero monthly fees.
- To switch to **PostgreSQL** (e.g. Neon.tech, Supabase free tier):
  Update `DATABASE_URL` in `backend/.env`:
  ```env
  DATABASE_URL="postgresql://user:password@ep-host.neon.tech/neondb?sslmode=require"
  ```
