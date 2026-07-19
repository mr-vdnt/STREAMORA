# Deployment Guide

## Prerequisites
- Docker and Docker Compose
- Secrets set up for JWT_SECRET and DOCKER_PASSWORD

## Staging Deployment
```bash
docker-compose -f docker-compose.yml up -d
```

## Production Deployment
Production relies on GitHub Actions. Pushes to `main` branch trigger the `Production Deployment Pipeline`, which builds the image and pushes to Docker Hub.
A webhook then alerts the target server to pull and restart.
