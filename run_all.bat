@echo off
echo ========================================================
echo AURORA AI - Microservices Startup Script
echo ========================================================

echo 1. Starting Ranking Service (Port 8001)...
start cmd /k ".\venv\Scripts\activate && set PYTHONPATH=. && uvicorn services.ranking.main:app --host 127.0.0.1 --port 8001"

echo 2. Starting Event Processor (Port 8002)...
start cmd /k ".\venv\Scripts\activate && set PYTHONPATH=. && uvicorn services.event-processor.main:app --host 127.0.0.1 --port 8002"

echo 3. Starting Graph RAG Service (Port 8003)...
start cmd /k ".\venv\Scripts\activate && set PYTHONPATH=. && uvicorn services.rag.main:app --host 127.0.0.1 --port 8003"

echo 4. Starting Orchestrator Agent and UI (Port 8004)...
start cmd /k ".\venv\Scripts\activate && set PYTHONPATH=. && uvicorn services.agent.main:app --host 127.0.0.1 --port 8004"

echo ========================================================
echo All services started in separate windows!
echo Access the UI at: http://127.0.0.1:8004
echo ========================================================
pause
