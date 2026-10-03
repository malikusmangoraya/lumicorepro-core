# =============================================================================
# LumicorePro — backend production image
# =============================================================================
# Single dependency install: the previous version ran `npm ci --only=production`
# twice (once in a `builder` stage, then again in the final stage before copying
# the builder's `node_modules` over it), so every image installed and discarded a
# full production dependency tree. `--only` is also the deprecated spelling of
# `--omit`.
#
# Changes beyond the cleanup:
#   * Runs as a non-root user (uid/gid 1001). The image previously ran as root,
#     so any RCE in a dependency owned the container's filesystem.
#   * `NODE_ENV=production` is set in the image, so `sequelize.sync` (development
#     only) can never run in a container that forgot to pass the variable.
#   * `init: true` is set in the Compose files so PID 1 forwards SIGTERM; the
#     server has a graceful-shutdown handler that needs that signal.
# =============================================================================

FROM node:20-alpine

# `dumb-init` reaps zombies and forwards signals. The Compose files also set
# `init: true`; either alone is sufficient, both together are harmless.
RUN apk add --no-cache dumb-init

ENV NODE_ENV=production \
    PORT=5000

WORKDIR /app

# Manifests first for a stable dependency layer.
COPY package.json package-lock.json ./

# `--omit=dev` keeps jest/supertest/nodemon out of production.
RUN npm ci --omit=dev --no-audit --no-fund && npm cache clean --force

COPY . .

# The server writes to uploads/ (multer) and logs/ (winston). Create them and
# hand ownership to the runtime user before dropping privileges.
RUN mkdir -p uploads logs tmp \
    && chown -R node:node /app \
    && chmod -R 755 uploads logs

USER node

EXPOSE 5000

# Node is guaranteed present, so the probe needs no extra binary.
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD node -e "require('http').get('http://127.0.0.1:5000/api/health', (r) => process.exit(r.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))"

ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "server.js"]
