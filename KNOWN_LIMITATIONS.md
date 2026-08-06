# NEXA Platform Known Limitations

## Current Constraints (v1.1.0)
1. **Background Job Rate Limits**: While RQ processes asynchronous tasks (like large PDF chunking), very high concurrent spikes might cause memory throttling on small instances. Horizontal worker scaling is required.
2. **WebSocket Fallback**: Long-polling fallback is not fully supported if the environment proxy strictly blocks HTTP Upgrade headers (WSS).
3. **Vision Processing Latency**: Large image uploads (close to the 15MB limit) may cause localized spikes in API response time prior to being routed to the background thread.
4. **Mobile Responsiveness**: The NEXA Studio is designed primarily for desktop/tablet use; mobile viewpoints on deep workflow editors are currently constrained.
