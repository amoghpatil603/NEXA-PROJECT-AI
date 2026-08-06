# NEXA Platform v1.1.0 Changelog

## [1.1.0] - 2026-08-05
### Added
- Redis integration for in-memory caching and session state management.
- Scalable background job processing system utilizing RQ for decoupled task execution.
- Advanced memory and reasoning engines for contextual understanding.
- Vision and Voice multi-modal integration.
- Studio dashboard telemetry and real-time monitoring via WebSockets.
- PostgreSQL database integration for persistent storage of telemetry and memory state.

### Changed
- Refactored `start.sh` to initialize Redis and RQ workers natively.
- API endpoints enhanced with caching layer to reduce inference latency.
- Consolidated background operations to scale gracefully across multiple decoupled worker nodes.

### Fixed
- Stabilized chat stream endpoints.
- Patched input validation vulnerabilities.
- Addressed MIME-type whitelisting on file uploads.
