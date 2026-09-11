# LumicorePro — Kubernetes Deployment Guide

## Prerequisites
- kubectl configured for your cluster
- cert-manager installed (for TLS)
- nginx ingress controller installed
- Container images pushed to `ghcr.io/lumicorepro/`

## Deployment Order

```bash
# 1. Create namespace
kubectl apply -f k8s/namespace.yaml

# 2. Create secrets (edit secret.yaml first with real base64 values)
kubectl apply -f k8s/secret.yaml

# 3. Create configmap
kubectl apply -f k8s/configmap.yaml

# 4. Deploy database + cache
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml

# 5. Deploy app
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml

# 6. Expose via ingress
kubectl apply -f k8s/ingress.yaml
```

## Apply Everything at Once
```bash
kubectl apply -f k8s/
```

## Useful Commands
```bash
# Watch rollout
kubectl rollout status deployment/lumicorepro-backend -n lumicorepro

# View logs
kubectl logs -f deployment/lumicorepro-backend -n lumicorepro

# Scale manually
kubectl scale deployment lumicorepro-backend --replicas=3 -n lumicorepro

# Check HPA
kubectl get hpa -n lumicorepro
```

## Secrets (base64 encode your values)
```bash
echo -n "your_secret_here" | base64
```
Edit `secret.yaml` with encoded values before applying.
