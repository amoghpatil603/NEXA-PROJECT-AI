class BaseTTSProvider:
    def speak(self, text):
        pass
    def stop(self):
        pass

class DummyTTSProvider(BaseTTSProvider):
    def speak(self, text):
        print(f"Speaking: {text}")
    def stop(self):
        print("Stopped speaking")
