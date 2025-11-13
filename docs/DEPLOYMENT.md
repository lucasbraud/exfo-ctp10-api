# Deployment Guide

Production deployment guide for EXFO CTP10 API using Docker, Kubernetes, and traditional methods.

## Table of Contents
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Traditional Deployment](#traditional-deployment)
- [Environment Configuration](#environment-configuration)
- [Production Best Practices](#production-best-practices)
- [Monitoring & Logging](#monitoring--logging)

---

## Docker Deployment

### Basic Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy project files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -e .

# Expose port
EXPOSE 8002

# Set environment variables
ENV MOCK_MODE=false
ENV LOG_LEVEL=INFO

# Run server
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8002"]
```

### Build and Run

```bash
# Build image
docker build -t ctp10-api:latest .

# Run in production mode (real hardware)
docker run -d \
  -p 8002:8002 \
  --name ctp10-api \
  -e MOCK_MODE=false \
  -e CTP10_IP=192.168.1.37 \
  ctp10-api:latest

# Run in mock mode (no hardware)
docker run -d \
  -p 8002:8002 \
  --name ctp10-api-mock \
  -e MOCK_MODE=true \
  ctp10-api:latest
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  ctp10-api:
    build: .
    ports:
      - "8002:8002"
    environment:
      - MOCK_MODE=false
      - CTP10_IP=192.168.1.37
      - CTP10_PORT=5025
      - AUTO_CONNECT=true
      - LOG_LEVEL=INFO
    restart: unless-stopped
    networks:
      - ctp10-network

  ctp10-api-mock:
    build: .
    ports:
      - "8003:8002"
    environment:
      - MOCK_MODE=true
      - LOG_LEVEL=DEBUG
    restart: unless-stopped
    networks:
      - ctp10-network

networks:
  ctp10-network:
    driver: bridge
```

Run:
```bash
docker-compose up -d
```

---

## Kubernetes Deployment

### Deployment Manifest

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ctp10-api
  namespace: production
spec:
  replicas: 1  # Single replica for hardware connection
  selector:
    matchLabels:
      app: ctp10-api
  template:
    metadata:
      labels:
        app: ctp10-api
    spec:
      containers:
      - name: ctp10-api
        image: ctp10-api:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8002
          name: http
        env:
        - name: MOCK_MODE
          value: "false"
        - name: CTP10_IP
          value: "192.168.1.37"
        - name: CTP10_PORT
          value: "5025"
        - name: AUTO_CONNECT
          value: "true"
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8002
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8002
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: ctp10-api
  namespace: production
spec:
  selector:
    app: ctp10-api
  ports:
  - protocol: TCP
    port: 8002
    targetPort: 8002
  type: ClusterIP
```

### Using ConfigMap for Configuration

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ctp10-config
  namespace: production
data:
  MOCK_MODE: "false"
  CTP10_IP: "192.168.1.37"
  CTP10_PORT: "5025"
  AUTO_CONNECT: "true"
  LOG_LEVEL: "INFO"
---
# Update deployment to use ConfigMap
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ctp10-api
spec:
  template:
    spec:
      containers:
      - name: ctp10-api
        envFrom:
        - configMapRef:
            name: ctp10-config
```

### Ingress for External Access

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ctp10-api
  namespace: production
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: ctp10-api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ctp10-api
            port:
              number: 8002
```

### Deploy to Kubernetes

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n production
kubectl logs -f deployment/ctp10-api -n production

# Port forward for testing
kubectl port-forward -n production svc/ctp10-api 8002:8002
```

---

## Traditional Deployment

### Systemd Service

```ini
# /etc/systemd/system/ctp10-api.service
[Unit]
Description=EXFO CTP10 API Server
After=network.target

[Service]
Type=simple
User=ctp10
Group=ctp10
WorkingDirectory=/opt/ctp10-api
Environment="MOCK_MODE=false"
Environment="CTP10_IP=192.168.1.37"
Environment="AUTO_CONNECT=true"
Environment="LOG_LEVEL=INFO"
ExecStart=/opt/ctp10-api/.venv/bin/fastapi run app/main.py --host 0.0.0.0 --port 8002
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ctp10-api
sudo systemctl start ctp10-api
sudo systemctl status ctp10-api
```

### Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/ctp10-api
server {
    listen 80;
    server_name ctp10-api.example.com;

    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://127.0.0.1:8002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

Enable:
```bash
sudo ln -s /etc/nginx/sites-available/ctp10-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Environment Configuration

### Production Environment Variables

```bash
# Production (real hardware)
export MOCK_MODE=false
export CTP10_IP=192.168.1.37
export CTP10_PORT=5025
export AUTO_CONNECT=true
export LOG_LEVEL=INFO
export API_PORT=8002
```

### Staging Environment

```bash
# Staging (mock mode for testing)
export MOCK_MODE=true
export AUTO_CONNECT=false
export LOG_LEVEL=DEBUG
export API_PORT=8002
```

### Using .env Files

**Production (.env.production):**
```bash
MOCK_MODE=false
CTP10_IP=192.168.1.37
CTP10_PORT=5025
AUTO_CONNECT=true
LOG_LEVEL=INFO
```

**Staging (.env.staging):**
```bash
MOCK_MODE=true
AUTO_CONNECT=false
LOG_LEVEL=DEBUG
```

Load specific env file:
```bash
# Copy environment-specific file
cp .env.production .env

# Run server
fastapi run app/main.py
```

---

## Production Best Practices

### Security

1. **Don't expose sensitive data:**
   ```bash
   # Use secrets management
   # Kubernetes secrets, Docker secrets, environment variables
   ```

2. **Use HTTPS:**
   ```python
   # In nginx or load balancer
   # Don't serve production API over HTTP
   ```

3. **Rate limiting:**
   ```python
   # Use slowapi or nginx rate limiting
   from slowapi import Limiter
   ```

4. **CORS configuration:**
   ```python
   # In app/main.py, limit origins in production
   allow_origins=["https://your-frontend.com"]
   ```

### Monitoring

1. **Health checks:**
   ```bash
   # Use /health endpoint
   curl http://localhost:8002/health
   ```

2. **Logging:**
   ```python
   # Set LOG_LEVEL=INFO in production
   # Set LOG_LEVEL=DEBUG only for troubleshooting
   ```

3. **Metrics:**
   ```python
   # Add prometheus metrics
   from prometheus_fastapi_instrumentator import Instrumentator
   Instrumentator().instrument(app).expose(app)
   ```

### High Availability

1. **Health checks:**
   - Liveness: `/health`
   - Readiness: `/health` (check hardware connection)

2. **Graceful shutdown:**
   - FastAPI handles SIGTERM gracefully
   - Cleanup in lifespan context manager

3. **Single replica for hardware:**
   - Only one instance should connect to CTP10
   - Use locks or leader election if scaling

### Backup & Recovery

1. **Configuration backup:**
   ```bash
   # Backup environment variables
   env | grep CTP10 > backup.env
   ```

2. **Database (if added):**
   ```bash
   # Regular backups of any persistent data
   ```

---

## Monitoring & Logging

### Structured Logging

```python
# Use structured logging in production
import structlog

logger = structlog.get_logger()
logger.info("event_name", key="value", extra_data=123)
```

### Log Aggregation

**Docker logs:**
```bash
docker logs -f ctp10-api
docker logs --since 30m ctp10-api
```

**Kubernetes logs:**
```bash
kubectl logs -f deployment/ctp10-api -n production
kubectl logs --tail=100 deployment/ctp10-api -n production
```

**Systemd logs:**
```bash
journalctl -u ctp10-api -f
journalctl -u ctp10-api --since "1 hour ago"
```

### Metrics Collection

**Prometheus example:**
```python
# Add to app/main.py
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

Access metrics: `http://localhost:8002/metrics`

### Alerts

**Sample alert rules:**
```yaml
# prometheus-rules.yml
groups:
- name: ctp10_alerts
  rules:
  - alert: CTP10APIDown
    expr: up{job="ctp10-api"} == 0
    for: 5m
    annotations:
      summary: "CTP10 API is down"

  - alert: CTP10HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    annotations:
      summary: "High error rate on CTP10 API"
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs ctp10-api

# Check if port is available
netstat -tulpn | grep 8002

# Verify environment variables
docker exec ctp10-api env | grep MOCK_MODE
```

### Connection Issues

```bash
# Check network connectivity from container
docker exec ctp10-api ping 192.168.1.37

# Verify CTP10 is accessible
curl http://localhost:8002/health
```

### Performance Issues

```bash
# Check resource usage
docker stats ctp10-api

# Kubernetes resource usage
kubectl top pod -n production
```

---

## Scaling Considerations

### Horizontal Scaling

⚠️ **Important:** CTP10 hardware can only have one connection at a time.

**Options:**
1. **Single instance** - Recommended for hardware mode
2. **Load balancer with sticky sessions** - If needed
3. **Mock mode only** - Can scale freely in mock mode

### Vertical Scaling

Resource requirements:
- **CPU:** Minimal (~100m)
- **Memory:** ~128Mi typical, 512Mi max
- **Network:** Depends on WebSocket usage

---

## Additional Resources

- **Usage Guide:** [docs/USAGE.md](USAGE.md)
- **Testing Guide:** [docs/TESTING.md](TESTING.md)
- **Main README:** [README.md](../README.md)
- **FastAPI Deployment:** https://fastapi.tiangolo.com/deployment/
- **Docker Best Practices:** https://docs.docker.com/develop/dev-best-practices/
