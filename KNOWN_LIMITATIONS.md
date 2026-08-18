# NEXA Known Limitations

1. **Context Window**: The custom 13.8M transformer engine supports a context length of 8,192 tokens. Extremely large document corpora require RAG chunking.
2. **Autonomous Workflow Timeout**: Long-running asynchronous workflows exceeding 24 hours require active worker node heartbeats and persistent volume storage.
3. **Sandbox Execution**: Python tool execution is strictly sandboxed; system-level kernel modules or raw network sockets cannot be accessed from within user sandbox containers.
