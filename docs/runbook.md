# Runbook & Troubleshooting

## High API Latency
1. Check Prometheus metrics for `streamora-api`.
2. Determine if LLM latency is high. If so, restart Ollama container.
3. Check Redis hit rate.

## Database Locked
1. SQLite operates in WAL mode. If `database is locked` appears, ensure timeout settings are applied.
2. Consider scaling down `MAX_GENERATOR_WORKERS`.
