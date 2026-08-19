# Tauri + React + Typescript

This template should help get you started developing with Tauri, React and Typescript in Vite.

## Recommended IDE Setup

- [VS Code](https://code.visualstudio.com/) + [Tauri](https://marketplace.visualstudio.com/items?itemName=tauri-apps.tauri-vscode) + [rust-analyzer](https://marketplace.visualstudio.com/items?itemName=rust-lang.rust-analyzer)

## Testing Guide

All lightweight unit tests and contract validation tests can be run using `pytest`.

### Prerequisites
Install testing dependencies:
```bash
pip install pytest numpy torch
```

### Running Tests
Run the test suites for any specific phase:
```bash
# Phase 2 (Trainer & Identity Engine)
python -m pytest tests/phase2 -v

# Phase 3 (Inference Interfaces)
python -m pytest tests/phase3 -v

# Phase 4 (Memory Contracts)
python -m pytest tests/phase4 -v

# Phase 5 (RAG Contracts)
python -m pytest tests/phase5 -v

# Phase 6 (Tool Contracts)
python -m pytest tests/phase6 -v

# Phase 7 (Agent Contracts)
python -m pytest tests/phase7 -v

# Phase 8 (Evaluation Scaffold)
python -m pytest tests/phase8 -v

# Phase 9 (Multimodal Contracts)
python -m pytest tests/phase9 -v

# Phase 10 (Engineering Hardening)
python -m pytest tests/phase10 -v
```

To run all tests:
```bash
python -m pytest tests/phase2 tests/phase3 tests/phase4 tests/phase5 tests/phase6 tests/phase7 tests/phase8 tests/phase9 tests/phase10 -v
```
