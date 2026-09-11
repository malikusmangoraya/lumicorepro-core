# LumiCorePro — Production Deployment Guide

This guide outlines deployment strategies for LumiCorePro across various cloud platforms and container orchestration engines.

---

## 1. Docker Compose (Single Host / VPS)

### Prerequisites
- Docker Engine 24+
- Docker Compose v2.20+
- Domain configured with DNS A-records

### Deployment Steps
1. Clone the repository and configure environment files:
   ```bash
   git clone https://github.com/your-org/lumicorepro-core.git
   cd lumicorepro-core
   cp .env.production .env
   cp backend/.env.production backend/.env
   ```

2. Build and launch all services:
   ```bash
   docker-compose --env-file backend/.env.production up -d --build
   ```

3. Initialize seed data (optional):
   ```bash
   docker exec -it lumicorepro-backend npm run seed
   ```

4. Verify service health:
   ```bash
   curl -i http://localhost:5000/api/health/detailed
   ```

---

## 2. Kubernetes Deployment (Production Cluster)

### Architecture
- **Ingress Controller**: NGINX Ingress or Traefik with TLS certificate termination (Cert-Manager)
- **Frontend Deployment**: 2+ replicas running Nginx static build
- **Backend Deployment**: 3+ replicas with Horizontal Pod Autoscaler (HPA)
- **Stateful Services**: MongoDB Atlas & AWS ElastiCache / Redis

### Sample Backend Deployment Manifest (`k8s/backend.yaml`)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lumicorepro-backend
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: lumicorepro-backend
  template:
    metadata:
      labels:
        app: lumicorepro-backend
    spec:
      containers:
        - name: backend
          image: lumicorepro/backend:1.0.0
          ports:
            - containerPort: 5000
          envFrom:
            - secretRef:
                name: lumicorepro-secrets
          readinessProbe:
            httpGet:
              path: /api/health
              port: 5000
            initialDelaySeconds: 10
            periodSeconds: 5
          resources:
            requests:
              cpu: "250m"
              memory: "512Mi"
            limits:
              cpu: "1000m"
              memory: "1Gi"
```

---

## 3. Cloud Provider Quick Deployments

### AWS (ECS / Fargate)
- Push images to Amazon ECR.
- Deploy tasks using ECS Fargate cluster with Application Load Balancer (ALB).
- Use Amazon DocumentDB / Atlas for MongoDB and ElastiCache for Redis.

### Vercel / Render / Railway
- **Frontend**: Deploy directly from Git repo on Vercel (`npm run build`, output: `dist`).
- **Backend**: Deploy backend folder to Render Web Service or Railway (`npm start`, port `5000`).

---

## 4. SSL & Security Checklist
- [x] Enforce TLS 1.3 with HTTPS redirect.
- [x] Configure strict CORS with production domain whitelist.
- [x] Set strong JWT and Session secret keys in cloud secret manager.
- [x] Restrict MongoDB network access via VPC peering / IP allowlist.
