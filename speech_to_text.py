class BaseSTTProvider:
    def start(self):
        pass
    def stop(self):
        pass

class DummySTTProvider(BaseSTTProvider):
    def start(self):
        return True
    def stop(self):
        return "Simulated transcribed text."
