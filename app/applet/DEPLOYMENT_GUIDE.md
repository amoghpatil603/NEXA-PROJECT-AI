# NEXA Deployment Guide

## Prerequisites
- Node.js 18+ & npm
- Docker & Docker Compose
- Kubernetes 1.24+ (for enterprise clusters)

## Local Development via Docker Compose
```bash
docker-compose up --build
```

## Production Kubernetes Deployment
1. Apply Kubernetes manifests:
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
```
2. Verify rollout status:
```bash
kubectl rollout status deployment/nexa-platform
```
