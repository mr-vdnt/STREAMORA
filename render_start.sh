#!/bin/bash
export PYTHONPATH=.
uvicorn services.ranking.main:app --host 127.0.0.1 --port 8001 &
uvicorn services.event-processor.main:app --host 127.0.0.1 --port 8002 &
uvicorn services.agent.main:app --host 0.0.0.0 --port $PORT
