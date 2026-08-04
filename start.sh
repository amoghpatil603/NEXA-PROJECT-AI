#!/bin/bash
# Start NGINX in background
cp nginx.conf /etc/nginx/nginx.conf
nginx -g "daemon off;" &

# Start Node.js server
cd /app
node dist/server.cjs
