# Free Tier Deployment Guide — Apex

This application is engineered to be deployed for **$0 / month** on modern cloud platforms.

---

## 1. Frontend: Cloudflare Pages (Recommended - 100% Free)

Cloudflare Pages provides unlimited bandwidth and worldwide edge caching on their free tier.

### Deployment Steps:

1. Push your repository to GitHub.
2. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/) ➔ **Workers & Pages**.
3. Click **Create Application** ➔ **Pages** ➔ **Connect to Git**.
4. Select your repository:
   - **Framework preset**: `Vite`
   - **Build command**: `npm run build`
   - **Build output directory**: `dist`
   - **Root directory**: `frontend` (or project root if single directory)
5. Click **Save and Deploy**. Your site is now live with free SSL!

### Alternative Frontend: Netlify or GitHub Pages

- **Netlify**: `netlify.toml` is already included. Simply drag-and-drop the `dist` folder or connect your Git repo.
- **GitHub Pages**: Enabled via GitHub Actions (`.github/workflows/deploy.yml`).

---

## 2. Backend: Render (Free Tier) or Fly.io

Deploy the Node.js/Express API server on a generous free tier.

### Option A: Render

1. Sign up at [https://render.com](https://render.com).
2. Click **New ➔ Blueprint** and select your GitHub repo.
3. Render will automatically read the included `render.yaml` configuration:
   - Automatically sets up Node.js runtime.
   - Runs `npm install && npm run build`.
   - Starts API server on port 5000.

### Option B: Fly.io

1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Run in backend directory:
   ```bash
   fly launch
   fly deploy
   ```
   (Uses the included `fly.toml` and `Dockerfile`).

---

## 3. Docker Deployment (Local & VPS)

To run the full stack locally with one command:

```bash
docker-compose up --build
```

This starts both frontend and backend in isolated, production-grade containers.
