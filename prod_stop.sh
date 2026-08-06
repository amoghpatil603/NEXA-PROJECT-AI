#!/bin/bash
echo "--- Initiating Graceful Shutdown ---"
kill -TERM $(lsof -t -i:5000)
echo "✅ Services terminated."
