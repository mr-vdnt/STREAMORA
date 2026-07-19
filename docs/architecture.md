# Streamora Production Platform Architecture

## Overview
Streamora is a modern AI-powered streaming discovery platform. It uses FastAPI for the backend API, SQLite for storage (abstracted via SQLAlchemy for future Postgres migration), and Redis for caching.

## Components
1. **API Gateway (Nginx)**: Handles TLS termination, rate limiting, and caching of static assets.
2. **Application Server (FastAPI)**: Runs core logic and AI orchestration.
3. **LLM Orchestrator (Ollama)**: Local LLM service.
4. **Database (SQLite)**: Stores users, history, watchlist.
5. **Cache (Redis)**: Speeds up heavy operations.

## Observability
- **Prometheus** for metrics.
- **Grafana** for dashboards.
- **OpenTelemetry** for distributed tracing.
