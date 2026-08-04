# Known Issues (Beta 1.0.0-beta.1)

1. **Memory Synchronization Latency**:
   - Issue: When heavy requests block the Node.js event loop, local vector embeddings take slightly longer to commit to the RAG database.
   - Workaround: Allow a few seconds after ending a long conversation before starting a highly contextual retrieval query.

2. **Mobile Voice Streaming in Simulator**:
   - Issue: iOS Simulators may occasionally drop the WebSpeech API stream.
   - Workaround: Test Voice capabilities on physical devices.

3. **Rate Limiter Strictness**:
   - Issue: SSE streams (Server-Sent Events) for real-time chat occasionally trip the Express Rate Limiter under heavy burst usage.
   - Workaround: We have increased the limit to 1000req/15m, but extreme multi-agent parallel workflows may still trigger a 429 Error. Wait 15 minutes to reset.

4. **Resource Consumption**:
   - Issue: Python ML pipeline caching models in RAM can consume up to 4-6GB locally.
   - Workaround: Offload to smaller quantized models if RAM is constrained.
