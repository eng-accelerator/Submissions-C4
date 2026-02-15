# Production Deployment Guide

## DevOps Incident Analysis Suite

This guide covers production deployment scenarios for the Multi-Agent DevOps Incident Analysis Suite.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Single Server Deployment](#single-server-deployment)
3. [Docker Swarm Deployment](#docker-swarm-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Cloud Deployments](#cloud-deployments)
6. [Security Hardening](#security-hardening)
7. [Monitoring & Logging](#monitoring--logging)

---

## Prerequisites

### Required
- Docker 20.10+
- 2 CPU cores minimum
- 2GB RAM minimum
- OpenRouter API key

### Recommended
- 4 CPU cores
- 4GB RAM
- SSL/TLS certificate
- Reverse proxy (NGINX/Traefik)

---

## Single Server Deployment

### Option 1: Docker Compose (Recommended)

#### Step 1: Create Production Environment File

```bash
# Create .env file
cat > .env << 'EOF'
# Required
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Optional - Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Optional - JIRA
JIRA_URL=https://your-company.atlassian.net
JIRA_USERNAME=bot@company.com
JIRA_API_TOKEN=your-jira-token-here
JIRA_PROJECT_KEY=OPS

# LLM Configuration
LLM_MODEL=openai/gpt-4o
EOF

# Secure the file
chmod 600 .env
```

#### Step 2: Deploy with Docker Compose

```bash
# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Step 3: Configure Reverse Proxy (NGINX)

```nginx
# /etc/nginx/sites-available/devops-incident-suite

upstream devops_incident_suite {
    server localhost:8501;
}

server {
    listen 80;
    server_name incidents.yourcompany.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name incidents.yourcompany.com;
    
    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    location / {
        proxy_pass http://devops_incident_suite;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for Streamlit
        proxy_read_timeout 86400;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/devops-incident-suite \
            /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Docker Swarm Deployment

### Step 1: Initialize Swarm

```bash
docker swarm init
```

### Step 2: Create Secrets

```bash
# Create secrets for sensitive data
echo "sk-or-v1-your-key" | docker secret create openrouter_api_key -
echo "https://hooks.slack.com/..." | docker secret create slack_webhook_url -
echo "your-jira-token" | docker secret create jira_api_token -
```

### Step 3: Create Stack File

```yaml
# docker-stack.yml
version: '3.8'

services:
  devops-incident-suite:
    image: devops-incident-suite:latest
    ports:
      - "8501:8501"
    secrets:
      - openrouter_api_key
      - slack_webhook_url
      - jira_api_token
    environment:
      - OPENROUTER_API_KEY_FILE=/run/secrets/openrouter_api_key
      - SLACK_WEBHOOK_URL_FILE=/run/secrets/slack_webhook_url
      - JIRA_API_TOKEN_FILE=/run/secrets/jira_api_token
      - JIRA_URL=https://your-company.atlassian.net
      - JIRA_USERNAME=bot@company.com
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
      update_config:
        parallelism: 1
        delay: 10s
        order: stop-first
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3

secrets:
  openrouter_api_key:
    external: true
  slack_webhook_url:
    external: true
  jira_api_token:
    external: true
```

### Step 4: Deploy Stack

```bash
docker stack deploy -c docker-stack.yml devops-incident-suite

# Check status
docker stack ps devops-incident-suite

# View logs
docker service logs -f devops-incident-suite_devops-incident-suite
```

---

## Kubernetes Deployment

### Step 1: Create Namespace

```bash
kubectl create namespace devops-incident-suite
```

### Step 2: Create Secrets

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: devops-incident-suite-secrets
  namespace: devops-incident-suite
type: Opaque
stringData:
  openrouter-api-key: "sk-or-v1-your-key-here"
  slack-webhook-url: "https://hooks.slack.com/..."
  jira-api-token: "your-jira-token"
  jira-username: "bot@company.com"
  jira-url: "https://your-company.atlassian.net"
```

Apply:
```bash
kubectl apply -f secrets.yaml
```

### Step 3: Create Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: devops-incident-suite
  namespace: devops-incident-suite
spec:
  replicas: 3
  selector:
    matchLabels:
      app: devops-incident-suite
  template:
    metadata:
      labels:
        app: devops-incident-suite
    spec:
      containers:
      - name: devops-incident-suite
        image: devops-incident-suite:latest
        ports:
        - containerPort: 8501
          name: http
        env:
        - name: OPENROUTER_API_KEY
          valueFrom:
            secretKeyRef:
              name: devops-incident-suite-secrets
              key: openrouter-api-key
        - name: SLACK_WEBHOOK_URL
          valueFrom:
            secretKeyRef:
              name: devops-incident-suite-secrets
              key: slack-webhook-url
        - name: JIRA_API_TOKEN
          valueFrom:
            secretKeyRef:
              name: devops-incident-suite-secrets
              key: jira-api-token
        - name: JIRA_USERNAME
          valueFrom:
            secretKeyRef:
              name: devops-incident-suite-secrets
              key: jira-username
        - name: JIRA_URL
          valueFrom:
            secretKeyRef:
              name: devops-incident-suite-secrets
              key: jira-url
        resources:
          requests:
            memory: "1Gi"
            cpu: "1"
          limits:
            memory: "2Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /_stcore/health
            port: 8501
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /_stcore/health
            port: 8501
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Step 4: Create Service

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: devops-incident-suite
  namespace: devops-incident-suite
spec:
  selector:
    app: devops-incident-suite
  ports:
  - port: 80
    targetPort: 8501
    protocol: TCP
  type: ClusterIP
```

### Step 5: Create Ingress

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: devops-incident-suite
  namespace: devops-incident-suite
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/websocket-services: "devops-incident-suite"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - incidents.yourcompany.com
    secretName: devops-incident-suite-tls
  rules:
  - host: incidents.yourcompany.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: devops-incident-suite
            port:
              number: 80
```

### Step 6: Deploy

```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

# Check status
kubectl get pods -n devops-incident-suite
kubectl get svc -n devops-incident-suite
kubectl get ingress -n devops-incident-suite
```

---

## Cloud Deployments

### AWS (ECS Fargate)

```bash
# Build and push to ECR
aws ecr create-repository --repository-name devops-incident-suite
docker tag devops-incident-suite:latest \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/devops-incident-suite:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/devops-incident-suite:latest

# Create task definition (use AWS Console or CLI)
# Deploy to ECS Fargate
```

### Google Cloud (Cloud Run)

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT-ID/devops-incident-suite

# Deploy to Cloud Run
gcloud run deploy devops-incident-suite \
  --image gcr.io/PROJECT-ID/devops-incident-suite \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENROUTER_API_KEY=sk-or-v1-xxx
```

### Azure (Container Instances)

```bash
# Build and push to ACR
az acr build --registry myregistry \
  --image devops-incident-suite:latest .

# Deploy to ACI
az container create \
  --resource-group myResourceGroup \
  --name devops-incident-suite \
  --image myregistry.azurecr.io/devops-incident-suite:latest \
  --dns-name-label devops-incident-suite \
  --ports 8501 \
  --environment-variables \
    OPENROUTER_API_KEY=sk-or-v1-xxx
```

---

## Security Hardening

### 1. Network Security

```yaml
# Restrict access with firewall rules
# Only allow:
- Port 443 (HTTPS) from internet
- Port 8501 from reverse proxy only
- Outbound to OpenRouter, Slack, JIRA APIs
```

### 2. Authentication

Add basic auth to NGINX:

```nginx
location / {
    auth_basic "Restricted Access";
    auth_basic_user_file /etc/nginx/.htpasswd;
    # ... rest of config
}
```

### 3. Rate Limiting

```nginx
# In nginx.conf
http {
    limit_req_zone $binary_remote_addr zone=one:10m rate=10r/s;
    
    # In server block
    location / {
        limit_req zone=one burst=20;
        # ... rest of config
    }
}
```

### 4. Container Security

```dockerfile
# Use specific version (not latest)
FROM python:3.12.1-slim

# Run as non-root
USER appuser

# Read-only filesystem
docker run --read-only ...
```

---

## Monitoring & Logging

### Prometheus Metrics

Add to deployment:

```yaml
# Add sidecar for metrics export
containers:
- name: prometheus-exporter
  image: prom/statsd-exporter
  ports:
  - containerPort: 9102
```

### Centralized Logging

```yaml
# Add logging driver
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
    
# Or use Fluentd/ELK stack
```

### Health Monitoring

```bash
# Add uptime monitoring (UptimeRobot, Pingdom, etc.)
# Monitor endpoint: https://incidents.yourcompany.com/_stcore/health
```

---

## Backup & Recovery

### Backup Strategy

1. **Configuration**: Store in Git repository
2. **Secrets**: Use secrets management (Vault, AWS Secrets Manager)
3. **Logs**: Archive to S3/GCS/Azure Blob

### Disaster Recovery

```bash
# Export Docker image
docker save devops-incident-suite:latest | gzip > backup.tar.gz

# Restore
docker load < backup.tar.gz
```

---

## Scaling Guidelines

### Vertical Scaling
- Increase CPU/Memory for single instance
- Good for: Low to medium traffic

### Horizontal Scaling
- Run multiple instances behind load balancer
- Good for: High traffic, high availability

### Auto-scaling

Kubernetes HPA:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: devops-incident-suite-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: devops-incident-suite
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs devops-incident-suite

# Common issues:
- Missing environment variables
- Port already in use
- Insufficient memory
```

### High memory usage
```bash
# Increase memory limit
docker update --memory 4g devops-incident-suite
```

### API rate limits
```bash
# Add retry logic
# Use multiple API keys
# Implement caching
```

---

## Production Checklist

- [ ] SSL/TLS certificate configured
- [ ] Secrets stored securely (not in code)
- [ ] Reverse proxy configured
- [ ] Health checks enabled
- [ ] Monitoring setup
- [ ] Logging configured
- [ ] Backup strategy in place
- [ ] Auto-scaling configured
- [ ] Rate limiting enabled
- [ ] Authentication enabled
- [ ] Firewall rules configured
- [ ] Regular security updates scheduled

---

**Deployment Complete!** 🚀

For support, refer to:
- README.md
- ARCHITECTURE.md
- QUICKSTART.md
