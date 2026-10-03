# =============================================================================
# LumicorePro — AI agent (FastAPI) production image
# =============================================================================
# Build context is the REPOSITORY ROOT with `dockerfile: ./ai-agent/Dockerfile`
# (see docker-compose.*.yml). A repo-root context is required because the agent
# reads repository-level assets from PROJECT_ROOT-relative paths derived from its
# own location (ai-agent/config/settings.py -> PROJECT_ROOT = parent of ai-agent):
#
#   PROJECT_ROOT/src/templates        -> /app/../src/templates   (UI templates)
#   PROJECT_ROOT/registry             -> /app/../registry        (templates.json)
#   PROJECT_ROOT/database/schemas     -> /app/../database/schemas
#
# Only those three small directories are copied alongside the agent itself, so
# the image stays small while PROJECT_ROOT still resolves. Excludes are in
# ai-agent/.dockerignore.
#
# Model/provider SDK heavyweights that the *serving* path never imports
# (torch, chromadb, sentence-transformers) are intentionally NOT installed: they
# add ~2 GB and several minutes of build time. Features needing them (RAG engine)
# degrade gracefully. Set INSTALL_HEAVY_ML=true to opt in.
# =============================================================================

FROM python:3.11-slim AS runtime

# INSTALL_HEAVY_ML=true adds chromadb + sentence-transformers (~2 GB). Off by
# default; turn on only if you need the RAG engine inside the container.
ARG INSTALL_HEAVY_ML=false

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

# Runtime system libraries:
#   curl        -> container healthcheck
#   libpq5      -> psycopg-style Postgres clients used by optional integrations
#   build-essential is deliberately absent: any dependency needing a compiler is
#   either pulled as a wheel or not installed.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependency layer first, for cache reuse across source edits.
COPY ai-agent/requirements.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt \
    && if [ "$INSTALL_HEAVY_ML" = "true" ]; then \
         python -m pip install "chromadb>=0.4.22" "sentence-transformers>=2.3.1"; \
       fi

# Application code plus the repository assets PROJECT_ROOT-relative lookups need.
COPY ai-agent/ /app/
COPY src/templates /app/../src/templates
COPY registry /app/../registry
COPY database/schemas /app/../database/schemas

# Non-root. UID/GID 10001 is outside the range any base image already uses.
# /app/database and /app/generated-projects are declared as volumes in the
# Compose files; the chown here is what lets the non-root user write them on
# first start (named volumes inherit the image's ownership at creation).
RUN groupadd --gid 10001 agent \
    && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin agent \
    && mkdir -p /app/database /app/generated-projects /app/logs \
    && chown -R agent:agent /app

USER agent

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/health || exit 1

# No --reload: that is a development-only flag and leaks the source watcher into
# production. Single worker because the agent keeps run state (pipeline store,
# telemetry, in-memory run registry) in the process — see docs/RUNBOOK.md
# "Scale the AI agent" before raising --workers.
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--log-level", "info"]
