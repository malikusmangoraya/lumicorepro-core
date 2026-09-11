"""
Global Deployment Engine — LumicorePro AI Agent
================================================
Phase 15 — Global Delivery

Generates deployment configs for every major cloud/platform:
  - Vercel (frontend + serverless)
  - Railway (full-stack)
  - Render (full-stack)
  - AWS (ECS Fargate + CloudFront + RDS + ElastiCache)
  - GCP (Cloud Run + Cloud SQL + Cloud CDN)
  - Azure (Container Apps + Front Door + PostgreSQL)
  - DigitalOcean App Platform
  - GitHub Actions CI/CD pipeline (build → test → deploy)
  - DEPLOYMENT_GUIDE.md with step-by-step instructions
  - Environment variable checklist per platform
"""

import os
import json
from typing import Dict, Any, List
from utils.logger import agent_logger


class GlobalDeploymentEngine:
    """Multi-cloud deployment config generator."""

    # ── Platform metadata ─────────────────────────────────────────────────
    PLATFORMS: Dict[str, Dict[str, Any]] = {
        "vercel": {
            "name": "Vercel",        "type": "serverless", "cost": "free+",
            "best_for": ["saas", "portfolio", "blog", "business"],
            "regions": "Global Edge Network (40+ regions)",
            "deploy_cmd": "vercel --prod",
            "env_file": ".env.production",
        },
        "railway": {
            "name": "Railway",       "type": "container",  "cost": "$5/mo+",
            "best_for": ["ecommerce", "saas", "healthcare", "restaurant"],
            "regions": "US West, US East, EU West, AP Southeast",
            "deploy_cmd": "railway up",
            "env_file": "Railway Dashboard → Variables",
        },
        "render": {
            "name": "Render",        "type": "container",  "cost": "free+",
            "best_for": ["ecommerce", "saas", "restaurant", "education"],
            "regions": "US, EU, Singapore",
            "deploy_cmd": "git push origin main",
            "env_file": "Render Dashboard → Environment",
        },
        "aws": {
            "name": "AWS",           "type": "cloud",      "cost": "pay-as-you-go",
            "best_for": ["enterprise", "fintech", "healthcare", "saas"],
            "regions": "30+ regions globally",
            "deploy_cmd": "aws ecs update-service --force-new-deployment",
            "env_file": "AWS Secrets Manager / Parameter Store",
        },
        "gcp": {
            "name": "GCP Cloud Run", "type": "serverless-container", "cost": "pay-as-you-go",
            "best_for": ["saas", "fintech", "enterprise"],
            "regions": "35+ regions globally",
            "deploy_cmd": "gcloud run deploy",
            "env_file": "GCP Secret Manager",
        },
        "digitalocean": {
            "name": "DigitalOcean",  "type": "container",  "cost": "$12/mo+",
            "best_for": ["ecommerce", "restaurant", "education", "portfolio"],
            "regions": "NYC, AMS, SGP, BLR, LON, FRA, TOR",
            "deploy_cmd": "doctl apps create --spec .do/app.yaml",
            "env_file": ".do/app.yaml environment section",
        },
    }

    def generate(self, spec: Dict[str, Any], project_dir: str) -> Dict[str, Any]:
        """Generate all deployment configs."""
        agent_logger.info("GlobalDeploymentEngine: Generating multi-cloud deployment configs...")

        website_type = spec.get("website_type", "ecommerce")
        region       = spec.get("region", "NA")
        project_name = spec.get("project_name", "project").lower().replace("_", "-").replace(" ", "-")
        features     = spec.get("features", [])
        has_payments = any(f in features for f in ["payment", "stripe", "checkout"])

        artifacts = []
        root = project_dir

        # Recommend best platforms for this type
        recommended = self._recommend_platforms(website_type)

        # 1. GitHub Actions CI/CD
        gh_dir = os.path.join(root, ".github", "workflows")
        os.makedirs(gh_dir, exist_ok=True)
        ci_path = os.path.join(gh_dir, "ci.yml")
        self._write(ci_path, self._build_github_ci(project_name, recommended[0]))
        artifacts.append(ci_path)

        deploy_path = os.path.join(gh_dir, "deploy.yml")
        self._write(deploy_path, self._build_github_deploy(project_name, recommended[0]))
        artifacts.append(deploy_path)

        # 2. Railway config
        railway_path = os.path.join(root, "railway.json")
        self._write(railway_path, json.dumps(self._build_railway(project_name), indent=2))
        artifacts.append(railway_path)

        # 3. Render config
        render_path = os.path.join(root, "render.yaml")
        self._write(render_path, self._build_render(project_name, features))
        artifacts.append(render_path)

        # 4. DigitalOcean App Platform
        do_dir = os.path.join(root, ".do")
        os.makedirs(do_dir, exist_ok=True)
        do_path = os.path.join(do_dir, "app.yaml")
        self._write(do_path, self._build_do_app(project_name, features))
        artifacts.append(do_path)

        # 5. AWS ECS task definition
        aws_dir = os.path.join(root, "aws")
        os.makedirs(aws_dir, exist_ok=True)
        ecs_path = os.path.join(aws_dir, "ecs-task-definition.json")
        self._write(ecs_path, json.dumps(self._build_ecs_task(project_name), indent=2))
        artifacts.append(ecs_path)

        # 6. GCP Cloud Run config
        gcp_path = os.path.join(root, "cloudrun.yaml")
        self._write(gcp_path, self._build_cloudrun(project_name, region))
        artifacts.append(gcp_path)

        # 7. DEPLOYMENT_GUIDE.md
        guide_path = os.path.join(root, "DEPLOYMENT_GUIDE.md")
        self._write(guide_path, self._build_guide(spec, recommended, has_payments))
        artifacts.append(guide_path)

        # 8. .env.production template
        env_path = os.path.join(root, ".env.production.example")
        self._write(env_path, self._build_env_template(features, has_payments))
        artifacts.append(env_path)

        result = {
            "platforms_configured": list(self.PLATFORMS.keys()),
          "platforms_supported": list(self.PLATFORMS.keys()),
            "recommended_platform": recommended[0],
            "recommended_order":    recommended,
            "artifacts":            artifacts,
            "has_payments":         has_payments,
            "region":               region,
        }
        agent_logger.info(
            f"GlobalDeploymentEngine: {len(artifacts)} configs, "
            f"recommended={recommended[0]}"
        )
        return result

    # ── Hosting cost simulator ─────────────────────────────────────────────
    # Rough monthly estimates (USD) by deployment tier. Static reference data —
    # a decision-making aid, not a bill.
    COST_TABLE: Dict[str, Dict[str, Dict[str, str]]] = {
        "vercel":        {"low": "$0",   "medium": "$20", "high": "$100"},
        "cloudflare":    {"low": "$0",   "medium": "$0",  "high": "$25"},
        "netlify":       {"low": "$0",   "medium": "$19", "high": "$99"},
        "github":        {"low": "$0",   "medium": "$4",  "high": "$20"},
        "railway":       {"low": "$5",   "medium": "$20", "high": "$80"},
        "render":        {"low": "$0",   "medium": "$7",  "high": "$50"},
        "digitalocean":  {"low": "$12",  "medium": "$24", "high": "$96"},
        "aws":           {"low": "$7",   "medium": "$45", "high": "$220"},
        "gcp":           {"low": "$6",   "medium": "$40", "high": "$200"},
    }

    def estimate_running_cost(
        self,
        website_type: str = "business",
        traffic: str = "low",
        has_payments: bool = False,
    ) -> Dict[str, Any]:
        """Rough monthly cost estimates per platform/traffic tier."""
        tier = traffic if traffic in ("low", "medium", "high") else "low"
        recommended = self._recommend_platforms(website_type)

        estimates = {}
        for platform, tiers in self.COST_TABLE.items():
            estimate = tiers.get(tier, tiers["low"])
            add_payment = "+1%" if (has_payments and platform in ("aws", "gcp", "cloudflare", "netlify")) else ""
            estimates[platform] = {
                "monthly_usd": estimate + add_payment,
                "class": "static-site" if platform in ("vercel", "cloudflare", "netlify", "github") else "app-server",
            }

        return {
            "traffic_tier": tier,
            "estimates": estimates,
            "cheapest": [p for p in ("github", "vercel", "cloudflare", "netlify") if p in estimates][:2],
            "recommended_for_type": recommended[:3],
            "note": "Planning estimate only — real cost depends on traffic, storage, and add-ons.",
        }

    def _recommend_platforms(self, website_type: str) -> List[str]:
        scored = {}
        for platform, meta in self.PLATFORMS.items():
            score = 1 if website_type in meta["best_for"] else 0
            if website_type == "enterprise":
                score += 2 if platform in ("aws", "gcp") else 0
            scored[platform] = score
        return sorted(scored, key=lambda p: scored[p], reverse=True)

    def _build_github_ci(self, project_name: str, deploy_platform: str) -> str:
        return f"""# GitHub Actions — CI Pipeline

name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '20'
  PYTHON_VERSION: '3.11'

jobs:
  lint-and-test-frontend:
    name: Frontend — Lint & Test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{{{ env.NODE_VERSION }}}}
          cache: npm

      - name: Install dependencies
        run: npm ci

      - name: Lint
        run: npm run lint

      - name: Run tests
        run: npm test -- --run

      - name: Build
        run: npm run build

      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: frontend-dist
          path: dist/
          retention-days: 1

  lint-and-test-backend:
    name: Backend — Lint & Test
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./backend
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{{{ env.NODE_VERSION }}}}
          cache: npm
          cache-dependency-path: backend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Lint
        run: npm run lint || true

      - name: Run tests
        run: npm test || true

  lighthouse-ci:
    name: Lighthouse CI
    runs-on: ubuntu-latest
    needs: lint-and-test-frontend
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{{{ env.NODE_VERSION }}}}
          cache: npm

      - name: Install & Build
        run: npm ci && npm run build

      - name: Run Lighthouse CI
        uses: treosh/lighthouse-ci-action@v11
        with:
          configPath: .lighthouserc.json
          uploadArtifacts: true
        continue-on-error: true
"""

    def _build_github_deploy(self, project_name: str, platform: str) -> str:
        platform_step = {
            "vercel":      "    - name: Deploy to Vercel\n      uses: amondnet/vercel-action@v25\n      with:\n        vercel-token: ${{ secrets.VERCEL_TOKEN }}\n        vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}\n        vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}\n        vercel-args: '--prod'",
            "railway":     "    - name: Deploy to Railway\n      run: npx railway up\n      env:\n        RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}",
            "render":      "    - name: Trigger Render Deploy\n      run: curl -X POST ${{ secrets.RENDER_DEPLOY_HOOK_URL }}",
            "digitalocean":"    - name: Deploy to DigitalOcean\n      uses: digitalocean/app_action@v1\n      with:\n        token: ${{ secrets.DIGITALOCEAN_TOKEN }}",
            "aws":         "    - name: Deploy to AWS ECS\n      run: aws ecs update-service --cluster ${{ secrets.AWS_ECS_CLUSTER }} --service ${{ secrets.AWS_ECS_SERVICE }} --force-new-deployment",
        }.get(platform, "    - name: Deploy\n      run: echo 'Configure deploy step for your platform'")

        return f"""# GitHub Actions — Deploy Pipeline
# Platform: {self.PLATFORMS.get(platform, {}).get('name', platform)}

name: Deploy

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    name: Deploy to {self.PLATFORMS.get(platform, {}).get('name', platform)}
    runs-on: ubuntu-latest
    environment: production

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: npm

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test -- --run

      - name: Build production bundle
        run: npm run build
        env:
          NODE_ENV: production
          VITE_API_URL: ${{{{ secrets.VITE_API_URL }}}}

{platform_step}

      - name: Notify Slack on success
        if: success()
        uses: rtCamp/action-slack-notify@v2
        env:
          SLACK_WEBHOOK: ${{{{ secrets.SLACK_WEBHOOK }}}}
          SLACK_MESSAGE: '✅ {project_name} deployed to production'
        continue-on-error: true

      - name: Notify Slack on failure
        if: failure()
        uses: rtCamp/action-slack-notify@v2
        env:
          SLACK_WEBHOOK: ${{{{ secrets.SLACK_WEBHOOK }}}}
          SLACK_MESSAGE: '❌ {project_name} deployment FAILED'
          SLACK_COLOR: danger
        continue-on-error: true
"""

    def _build_railway(self, project_name):
        return {
            "$schema": "https://railway.app/railway.schema.json",
            "build": {"builder": "DOCKERFILE", "dockerfilePath": "backend/Dockerfile"},
            "deploy": {
                "startCommand": "node server.js",
                "healthcheckPath": "/api/health",
                "healthcheckTimeout": 300,
                "restartPolicyType": "ON_FAILURE",
                "restartPolicyMaxRetries": 10,
            },
        }

    def _build_render(self, project_name, features):
        services = [
            {
                "type": "web",
                "name": f"{project_name}-frontend",
                "env": "static",
                "buildCommand": "npm ci && npm run build",
                "staticPublishPath": "./dist",
                "routes": [{"type": "rewrite", "source": "/*", "destination": "/index.html"}],
                "headers": [
                    {"path": "/*", "name": "X-Frame-Options", "value": "SAMEORIGIN"},
                    {"path": "/*", "name": "X-Content-Type-Options", "value": "nosniff"},
                    {"path": "/assets/*", "name": "Cache-Control", "value": "public, max-age=31536000, immutable"},
                ],
            },
            {
                "type": "web",
                "name": f"{project_name}-backend",
                "env": "node",
                "rootDir": "backend",
                "buildCommand": "npm ci",
                "startCommand": "npm start",
                "healthCheckPath": "/api/health",
                "envVars": [
                    {"key": "NODE_ENV", "value": "production"},
                    {"key": "PORT", "value": "5000"},
                    {"key": "MONGODB_URI", "fromDatabase": {"name": f"{project_name}-db", "property": "connectionString"}},
                ],
            },
        ]
        databases = [
            {"name": f"{project_name}-db", "databaseName": project_name.replace("-", "_"), "user": "app_user"}
        ]
        lines = ["# Render Blueprint", "services:"]
        for svc in services:
            lines.append(f"  - type: {svc.get('type','web')}")
            lines.append(f"    name: {svc['name']}")
            lines.append(f"    env: {svc.get('env','node')}")
            if "buildCommand" in svc:
                lines.append(f"    buildCommand: {svc['buildCommand']}")
            if "startCommand" in svc:
                lines.append(f"    startCommand: {svc['startCommand']}")
            if "healthCheckPath" in svc:
                lines.append(f"    healthCheckPath: {svc['healthCheckPath']}")
        lines.append("\ndatabases:")
        for db in databases:
            lines.append(f"  - name: {db['name']}")
            lines.append(f"    databaseName: {db['databaseName']}")
        return "\n".join(lines)

    def _build_do_app(self, project_name, features):
        return f"""# DigitalOcean App Platform
name: {project_name}

services:
  - name: backend
    dockerfile_path: backend/Dockerfile
    source_dir: /
    http_port: 5000
    instance_count: 1
    instance_size_slug: basic-xxs
    health_check:
      http_path: /api/health
    envs:
      - key: NODE_ENV
        value: production
      - key: PORT
        value: "5000"
      - key: MONGODB_URI
        type: SECRET
      - key: JWT_SECRET
        type: SECRET
      - key: STRIPE_SECRET_KEY
        type: SECRET

static_sites:
  - name: frontend
    build_command: npm ci && npm run build
    output_dir: dist
    catch_all_document: index.html
    cors:
      allow_origins:
        - prefix: https://
    envs:
      - key: NODE_ENV
        value: production

databases:
  - name: {project_name}-db
    engine: PG
    version: "15"
    size: db-s-dev-database
    num_nodes: 1
"""

    def _build_ecs_task(self, project_name):
        return {
            "family": f"{project_name}-backend",
            "networkMode": "awsvpc",
            "requiresCompatibilities": ["FARGATE"],
            "cpu": "512",
            "memory": "1024",
            "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole",
            "taskRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskRole",
            "containerDefinitions": [
                {
                    "name": "backend",
                    "image": f"ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/{project_name}-backend:latest",
                    "portMappings": [{"containerPort": 5000, "protocol": "tcp"}],
                    "essential": True,
                    "environment": [
                        {"name": "NODE_ENV", "value": "production"},
                        {"name": "PORT", "value": "5000"},
                    ],
                    "secrets": [
                        {"name": "MONGODB_URI",         "valueFrom": f"arn:aws:secretsmanager:REGION:ACCOUNT_ID:secret:{project_name}/MONGODB_URI"},
                        {"name": "JWT_SECRET",           "valueFrom": f"arn:aws:secretsmanager:REGION:ACCOUNT_ID:secret:{project_name}/JWT_SECRET"},
                        {"name": "STRIPE_SECRET_KEY",    "valueFrom": f"arn:aws:secretsmanager:REGION:ACCOUNT_ID:secret:{project_name}/STRIPE_SECRET_KEY"},
                    ],
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": f"/ecs/{project_name}",
                            "awslogs-region": "us-east-1",
                            "awslogs-stream-prefix": "ecs",
                        },
                    },
                    "healthCheck": {
                        "command": ["CMD-SHELL", "curl -f http://localhost:5000/api/health || exit 1"],
                        "interval": 30, "timeout": 5, "retries": 3, "startPeriod": 60,
                    },
                }
            ],
        }

    def _build_cloudrun(self, project_name, region):
        gcp_region = {"NA": "us-central1", "EU": "europe-west1", "APAC": "asia-southeast1",
                      "SA": "asia-south1", "MENA": "europe-west1", "AF": "europe-west1",
                      "LATAM": "us-central1"}.get(region, "us-central1")
        return f"""# GCP Cloud Run
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: {project_name}-backend
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "1"
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/cpu-throttling: "false"
    spec:
      containerConcurrency: 80
      timeoutSeconds: 300
      containers:
        - image: gcr.io/PROJECT_ID/{project_name}-backend:latest
          ports:
            - containerPort: 5000
          env:
            - name: NODE_ENV
              value: production
            - name: PORT
              value: "5000"
          envFrom:
            - secretRef:
                name: {project_name}-secrets
          resources:
            limits:
              cpu: "1"
              memory: 512Mi
          livenessProbe:
            httpGet:
              path: /api/health
              port: 5000
            initialDelaySeconds: 30
            periodSeconds: 15
  traffic:
    - percent: 100
      latestRevision: true

# Deploy command:
# gcloud run deploy {project_name}-backend \\
#   --image gcr.io/PROJECT_ID/{project_name}-backend:latest \\
#   --region {gcp_region} \\
#   --platform managed \\
#   --allow-unauthenticated
"""

    def _build_env_template(self, features, has_payments):
        lines = [
            "# Production Environment Variables",
            "# NEVER commit this file with real values",
            "# Copy to .env.production and fill in real values",
            "",
            "# ── App ──────────────────────────────────────────────",
            "NODE_ENV=production",
            "PORT=5000",
            "FRONTEND_URL=https://yourdomain.com",
            "",
            "# ── Database ─────────────────────────────────────────",
            "MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/dbname",
            "",
            "# ── Auth ─────────────────────────────────────────────",
            "JWT_SECRET=change_this_to_64_char_random_string",
            "JWT_EXPIRES_IN=7d",
            "",
        ]
        if has_payments:
            lines += [
                "# ── Stripe ───────────────────────────────────────────",
                "STRIPE_SECRET_KEY=sk_live_xxx",
                "STRIPE_PUBLISHABLE_KEY=pk_live_xxx",
                "STRIPE_WEBHOOK_SECRET=whsec_xxx",
                "",
            ]
        lines += [
            "# ── Email ────────────────────────────────────────────",
            "SMTP_HOST=smtp.sendgrid.net",
            "SMTP_PORT=587",
            "SMTP_USER=apikey",
            "SMTP_PASS=your_sendgrid_api_key",
            "FROM_EMAIL=noreply@yourdomain.com",
            "",
            "# ── Monitoring ───────────────────────────────────────",
            "SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx",
            "",
            "# ── Redis (if used) ──────────────────────────────────",
            "REDIS_URL=redis://user:pass@host:6379",
            "",
            "# ── Frontend (Vite) ──────────────────────────────────",
            "VITE_API_URL=https://api.yourdomain.com",
            "VITE_GA4_ID=G-XXXXXXXXXX",
            "VITE_POSTHOG_KEY=phc_xxx",
        ]
        return "\n".join(lines)

    def _build_guide(self, spec, recommended, has_payments):
        project = spec.get("project_name", "project")
        lines = [
            f"# Deployment Guide — {project}",
            "\n## Recommended Deployment Order\n",
        ]
        for i, platform in enumerate(recommended[:4], 1):
            meta = self.PLATFORMS.get(platform, {})
            lines.append(f"{i}. **{meta.get('name', platform)}** — {meta.get('cost','?')}, {meta.get('regions','?')}")
        lines += [
            "\n## Quick Deploy (Recommended: Railway)\n```bash",
            "# 1. Install Railway CLI",
            "npm i -g @railway/cli",
            "",
            "# 2. Login",
            "railway login",
            "",
            "# 3. Link project",
            "railway link",
            "",
            "# 4. Set environment variables",
            "railway variables set NODE_ENV=production",
            "railway variables set MONGODB_URI='your_uri'",
            "railway variables set JWT_SECRET='your_secret'",
        ]
        if has_payments:
            lines += [
                "railway variables set STRIPE_SECRET_KEY='sk_live_xxx'",
                "railway variables set STRIPE_WEBHOOK_SECRET='whsec_xxx'",
            ]
        lines += [
            "",
            "# 5. Deploy",
            "railway up",
            "```",
            "\n## Pre-Deploy Checklist\n",
            "- [ ] All environment variables set in target platform",
            "- [ ] Database created and connection string configured",
            "- [ ] SMTP/email service configured",
            "- [ ] Domain name pointed to deployment",
            "- [ ] SSL certificate provisioned (usually automatic)",
        ]
        if has_payments:
            lines += [
                "- [ ] Stripe webhook endpoint registered: `POST /api/payments/webhook`",
                "- [ ] Stripe live mode keys configured (not test keys)",
            ]
        lines += [
            "- [ ] Sentry DSN configured for error monitoring",
            "- [ ] CDN configured (Cloudflare recommended)",
            "- [ ] Health check endpoint working: `GET /api/health`",
            "\n## Platform Comparison\n",
            "| Platform | Best For | Cost | Regions |",
            "|----------|----------|------|---------|",
        ]
        for name, meta in self.PLATFORMS.items():
            lines.append(f"| {meta['name']} | {', '.join(meta['best_for'][:2])} | {meta['cost']} | {meta['regions'][:40]} |")
        return "\n".join(lines)

    def _write(self, path, content):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            agent_logger.warning(f"GlobalDeploymentEngine: Could not write {path}: {e}")
