#!/bin/bash
echo "--- Starting NEXA Production Stack ---"
# Start API Server in background
python /content/NEXA-PROJECT-AI/api_chat_runner.py &
API_PID=$!

# Health Monitoring Loop
echo "Monitoring API health..."
for i in {1..30}; do
    if curl -s http://localhost:5000/health | grep -q 'READY'; then
        echo "✅ API is READY"
        break
    fi
    sleep 2
done

# Start UI / Desktop App (Dev Server in build mode)
cd /content/NEXA-PROJECT-AI
npm install && npm run dev
