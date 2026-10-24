# syntax=docker/dockerfile:1
# =============================================================================
# LumicorePro — single-service full-stack image
# =============================================================================
# One container serves the SPA, the Express API, uploaded files AND the Socket.IO
# upgrade on the SAME origin/port. That removes the CORS split and the two-deploy
# dance Vercel/Netlify force on a separate Express backend.
#
# Deploy targets: Render (render.yaml), Railway (railway.json), Fly.io, any VPS.
#
# Build args (Vite inlines VITE_* at build time):
#   VITE_API_URL  Leave EMPTY: the frontend calls a relative /api path and the
#                 same container answers it. A full origin would force CORS.
#   VITE_APP_ENV  production
# =============================================================================

# ── Stage 1: build the SPA ───────────────────────────────────────────────────
FROM node:20-alpine AS frontend

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY index.html vite.config.js tailwind.config.js postcss.config.js jsconfig.json ./
COPY public ./public
COPY src ./src

ARG VITE_API_URL=""
ARG VITE_APP_ENV="production"
ENV VITE_API_URL=$VITE_API_URL \
    VITE_APP_ENV=$VITE_APP_ENV

RUN npm run build

# ── Stage 2: backend production dependencies ─────────────────────────────────
FROM node:20-alpine AS backend-deps

WORKDIR /app

COPY backend/package.json backend/package-lock.json ./
RUN npm ci --omit=dev --no-audit --no-fund && npm cache clean --force

# ── Stage 3: runtime (API + SPA + WebSocket) ─────────────────────────────────
FROM node:20-alpine

RUN apk add --no-cache dumb-init

ENV NODE_ENV=production \
    PORT=5000 \
    SERVE_FRONTEND=true

# Keep the repository's backend/ + dist/ layout so `path.join(__dirname, '..', 'dist')`
# in server.js resolves exactly as it does on a dev machine.
WORKDIR /app/backend

COPY --from=backend-deps /app/node_modules ./node_modules
COPY backend/package.json ./package.json
COPY backend/ ./
COPY --from=frontend /app/dist /app/dist

RUN mkdir -p uploads logs tmp \
    && chown -R node:node /app \
    && chmod -R 755 uploads logs

USER node

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD node -e "require('http').get('http://127.0.0.1:5000/api/health', (r) => process.exit(r.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))"

ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "server.js"]
