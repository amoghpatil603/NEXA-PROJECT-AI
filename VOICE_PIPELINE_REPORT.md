# Voice Pipeline Report

## Execution Flow
1. **Audio Capture**: The user activates the microphone via the `VoiceRecorder` UI.
2. **Streaming STT**: The browser's Web Speech API natively buffers and streams audio to a recognition engine in real-time, yielding `interim` and `final` transcripts.
3. **Chat Engine Injection**: The final transcribed string is injected into the prompt input box and sent to the server.
4. **Backend Processing**: The transcription routes through the standard text pipeline, updating `MemoryEngine` and interacting with the `RAGEngine` before yielding an LLM completion.
5. **TTS Playback**: The frontend `VoicePlayer` converts the Markdown response back into speech, synthesizing audio output through the device speakers.

## Advantages
- True streaming nature reduces latency.
- Removes heavy lifting from the Express/Python backend, drastically reducing server costs.
- Fully supports existing Chat and Agent workflows without duplicating routing logic.
