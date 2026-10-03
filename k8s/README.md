# Kubernetes manifests — READ THIS FIRST

## Status: secondary target, honest about it

The canonical production topology for this application is **Docker Compose on a
single VPS** with nginx serving the static React build. That is what
`docs/DEPLOYMENT.md` describes, what `.github/workflows/deploy.yml` deploys, and
what has actually been exercised.

The manifests in this directory describe the **same application** on Kubernetes,
so they are not a different product and are not abandoned — but:

* they are **not** applied by CI and **not** covered by any test,
* they have **not** been applied to a live cluster by this repository's
  automation,
* several prerequisites live outside this directory (Ingress controller,
  cert-manager, an RWX storage class).

Anything that could not be verified is marked in a comment at the point where it
matters. Treat `kubectl apply` here as a starting point you must watch, not as a
deployment you can trust blind.

## What changed and why

| File | Change |
|------|--------|
| `configmap.yaml` | Added `DATABASE_URL` and `REDIS_URL`. Without `DATABASE_URL` the backend throws at boot in production (`backend/config/database.js`), so the pod would have crash-looped against a Postgres that created a database nothing could reach. |
| `postgres-deployment.yaml` | Removed a **duplicate** Redis StatefulSet + `redis-service`. Redis is now defined once, in `redis-deployment.yaml`. |
| `redis-deployment.yaml` | Probes now authenticate (`redis-cli -a`); a bare `ping` returns NOAUTH once `--requirepass` is set, which would have restart-looped the container. Strategy set to `Recreate` (RWO volume). |
| `secret.example.yaml` | **New.** Documents the required keys and the `kubectl create secret` command. |
| `secret.yaml` | No longer contains a Secret. It committed base64 `change_me` values, and `kubectl apply -f k8s/` would have created a cluster whose JWT secret is published in git. |
| `ai-agent-deployment.yaml` | **New.** `configmap.yaml` pointed `AI_AGENT_URL` at `http://ai-agent:8000` but no such Service existed, so every AI endpoint would have 502'd. |
| `backend-deployment.yaml` | Pinned image placeholder tag (was `:latest`), non-root security context, added `POSTGRES_PASSWORD`/`REDIS_PASSWORD` env entries (the kubelet only expands `$(VAR)` inside ConfigMap values when a variable of that exact name exists in the container env), dropped the unused `MONGODB_URI`, added a `PodDisruptionBudget` and anti-affinity. |
| `frontend-deployment.yaml` | Pinned tag, probes fixed (the image serves on **8080**, not 80, and exposes `/healthz.txt`), added a `PodDisruptionBudget`. |
| `ingress.yaml` | Added the same-origin **`/api`, `/socket.io`, `/uploads`, `/api-docs`** routes to `backend-service`. Without them the SPA's `/api` calls were answered by the frontend's index.html fallback. Added Socket.IO affinity annotations and HPA scale behaviour. |

## Prerequisites

- `kubectl` configured for the target cluster
- ingress-nginx (the annotations in `ingress.yaml` are ingress-nginx specific)
- cert-manager with a `ClusterIssuer` named `letsencrypt-prod`
- a storage class named `standard` (GKE/EKS default naming) that supports
  `ReadWriteMany` for `backend-uploads-pvc`
- images published to `ghcr.io/<owner>/lumicorepro-core-{backend,frontend,ai-agent}`
  — `.github/workflows/deploy.yml` pushes them on a `v*.*.*` tag

## Apply order

The Secret must exist **before** the Deployments, or every pod fails with
`CreateContainerConfigError`. Create it imperatively — never from a committed
file.

```bash
# 1. Namespace
kubectl apply -f k8s/namespace.yaml

# 2. Secrets (values never touch the repository)
kubectl -n lumicorepro create secret generic lumicorepro-secrets \
  --from-literal=POSTGRES_PASSWORD="$(openssl rand -base64 32)" \
  --from-literal=REDIS_PASSWORD="$(openssl rand -base64 32)" \
  --from-literal=JWT_SECRET="$(openssl rand -hex 48)" \
  --from-literal=JWT_REFRESH_SECRET="$(openssl rand -hex 48)"
#    Full key list and rotation procedure: k8s/secret.example.yaml

kubectl -n lumicorepro create secret generic lumicorepro-ai-secrets \
  --from-literal=GROK_API_KEY="" \
  --from-literal=GEMINI_API_KEY="" \
  --from-literal=OPENAI_API_KEY="" \
  --from-literal=DEEPSEEK_API_KEY="" \
  --from-literal=OPENROUTER_API_KEY="" \
  --from-literal=GITHUB_TOKEN=""

kubectl -n lumicorepro create configmap lumicorepro-ai-config \
  --from-literal=ACTIVE_AI_PROVIDER=grok

# 3. Config, data stores, then the app
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/ai-agent-deployment.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/ingress.yaml

# 4. Wait and verify
kubectl -n lumicorepro rollout status deploy/lumicorepro-backend
kubectl -n lumicorepro get pvc        # all Bound, including backend-uploads-pvc
kubectl -n lumicorepro get pdb,hpa
```

**Do not run `kubectl apply -f k8s/`.** It also reads `secret.yaml` and
`secret.example.yaml`, which are documentation-only templates. Apply the files
explicitly, in the order above. (Keep image tags pinned to a released version —
the placeholder `1.0.0` must be replaced first.)

`secret.yaml` and `secret.example.yaml` contain no usable credential; they exist
to document the required keys and to keep a stale copy of the old placeholder
Secret from being re-applied from a developer's checkout or a CI cache.

## Useful commands

```bash
# Rollout / logs
kubectl -n lumicorepro rollout status deploy/lumicorepro-backend
kubectl -n lumicorepro logs -f deploy/lumicorepro-backend
kubectl -n lumicorepro logs -f deploy/ai-agent

# Scale manually (the HPA will fight this — use it to test, not to autoscale)
kubectl -n lumicorepro scale deployment lumicorepro-backend --replicas=3

# Autoscalers / disruption budgets
kubectl -n lumicorepro get hpa,pdb

# Restart after rotating a Secret
kubectl -n lumicorepro rollout restart deploy/lumicorepro-backend
```

## Secrets

Create them with `kubectl create secret` (see above) or a sealed-secrets /
external-secrets operator. Never edit a YAML file with real values and commit it.
`k8s/secret.example.yaml` documents every required and optional key and the
rotation procedure.

## Known gaps

1. **Base schema.** The same open item as in Compose: the running schema comes
   from the Sequelize models, and production runs with `sequelize.sync`
   disabled, so `database/migrations/*` assumes the base tables already exist.
   See `docs/DEPLOYMENT.md` § Migrations. Nothing in this directory creates
   tables.
2. **`backend-uploads-pvc` is `ReadWriteMany`.** EKS's default `gp2`/`gp3`
   classes are RWO-only, so that PVC stays `Pending` there. See the comment on
   the claim in `backend-deployment.yaml`.
3. **Socket.IO affinity** is configured through ingress-nginx cookie affinity but
   is unverified across more than one replica. Verify it explicitly — a broken
   affinity presents as "notifications stopped arriving", not as an error.
4. **The AI agent must stay at 1 replica.** It keeps run state in-process and
   writes SQLite on a RWO volume. See `docs/RUNBOOK.md` § "Scale the AI agent".
5. **No NetworkPolicy.** Postgres and Redis are ClusterIP-only, which is all the
   manifests control; a default-deny NetworkPolicy is recommended but is
   CNI-dependent (silently ignored where not enforced) and has not been added.
