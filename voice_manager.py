import threading

class VoiceManager:
    def __init__(self, stt_provider, tts_provider):
        self.stt_provider = stt_provider
        self.tts_provider = tts_provider
        self.is_recording = False
        self.is_speaking = False

    def start_recording(self):
        self.is_recording = True
        return self.stt_provider.start()

    def stop_recording(self):
        self.is_recording = False
        return self.stt_provider.stop()

    def speak(self, text):
        self.is_speaking = True
        self.tts_provider.speak(text)
        self.is_speaking = False

    def stop_speaking(self):
        self.tts_provider.stop()
        self.is_speaking = False
