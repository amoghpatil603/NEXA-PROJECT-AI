# Bug Report & Resolutions

## Identified Issues During QA

### 1. `Mic` not defined in StudioMain.tsx
- **Severity**: High (Compilation Failure)
- **Description**: The Vite build failed because the `Mic` icon was referenced but not imported in `src/studio/StudioMain.tsx`.
- **Resolution**: Fixed in Phase P5 by updating the `lucide-react` import statement. Confirmed working.

### 2. Rate Limiting False Positives on SSE Streams
- **Severity**: Low
- **Description**: Long-running streaming requests were occasionally being counted multiple times by the rate limiter under heavy concurrency.
- **Resolution**: Streamlined the rate limiter config in `server.ts` to correctly handle persistent connections.

### 3. File Upload Directory Missing
- **Severity**: Medium
- **Description**: The Docker container failed to upload images in some environments because the `/app/uploads` folder was not guaranteed to exist.
- **Resolution**: Added `RUN mkdir -p uploads data model_cache` to the `Dockerfile` to ensure persistent volume mount targets exist.

## Current Known Limitations
- Heavy local LLMs (e.g. 7B parameters) will cause significant CPU usage when GPU acceleration is unavailable.
- STT WebSpeech API is browser-dependent; Firefox may have reduced functionality compared to Chrome/Edge.

All blocking issues have been resolved.
