#!/bin/bash
echo "--- Starting NEXA Production Stack ---"
# Set PYTHONPATH to root so backend package is findable
export PYTHONPATH=$PYTHONPATH:.

# Start FastAPI API Server in background
python3 backend/api/ai_service.py &
API_PID=$!

# Health Monitoring Loop
echo "Monitoring API health on port 8000..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health | grep -q 'ok'; then
        echo "✅ NEXA AI Service is READY"
        break
    fi
    sleep 2
done

# Start UI / Desktop App
npm run dev
