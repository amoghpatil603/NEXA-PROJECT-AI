#!/bin/bash
# Start Redis in background
redis-server --daemonize yes

# Start NGINX in background
cp nginx.conf /etc/nginx/nginx.conf
nginx -g "daemon off;" &

# Set PYTHONPATH so backend package is findable
export PYTHONPATH=$PYTHONPATH:.

# Start RQ worker in background
rq worker nexa_tasks &

# Start FastAPI AI Service in background
python3 backend/api/ai_service.py &

# Wait for FastAPI to be ready
echo "Waiting for NEXA AI Service..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health | grep -q 'ok'; then
        echo "✅ NEXA AI Service is READY"
        break
    fi
    sleep 2
done

# Start Node.js server
cd /app
node dist/server.cjs
