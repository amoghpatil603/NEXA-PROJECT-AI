# NEXA Input Validation Report

## Overview
NEXA v1.1.7 introduces comprehensive request validation across all public and internal service endpoints to protect against parameter pollution, buffer overflow attempts, and prompt injection vectors.

## Endpoint Enforcements

### 1. `/chat` & `/chat/stream`
- **Message Field**: Required non-empty string; enforced maximum length of 10,000 characters.
- **System Prompt**: Optional string constrained to a maximum of 4,000 characters.
- **History Array**: Truncated to the last 50 dialogue turns to prevent memory overflow.
- **Inference Parameters**:
  - `max_tokens`: Clamped between 1 and 2048.
  - `temperature`: Clamped between 0.0 and 2.0.
  - `top_k`: Clamped between 1 and 100.
  - `top_p`: Clamped between 0.0 and 1.0.

### 2. `/vision` & `/api/upload`
- **File Size Limit**: Strictly enforced 15MB limit.
- **Allowed Formats**: `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`, `.pdf`, `.txt`, `.md`, `.json`, `.csv`.
- **Blocked Formats**: `.exe`, `.sh`, `.bat`, `.cmd`, `.py`, `.js`, `.php`, `.pl`, `.dll`, `.so`, `.elf`, `.html`, `.svg`.
- **Filename Sanitization**: Removes null bytes, path traversal sequences (`../`), and non-alphanumeric characters.

### 3. `/voice`
- **Transcript Text**: Validated type and clamped to a maximum length of 2,000 characters.

## Threat Scanning
Integrated rule-based threat detection scanning prompt inputs for known injection and execution patterns (`ignore previous instructions`, `system override`, `rm -rf`, `drop table`, `<script>`).
