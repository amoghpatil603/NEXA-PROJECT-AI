import sys
content = open("backend/models/chat_engine.py").read()

content = content.replace("import torch\nimport torch.nn.functional as F\n", """try:
    import torch
    import torch.nn.functional as F
except ImportError:
    torch = None
    F = None
""")

content = content.replace(
"""        self.pad_token_id = DEFAULT_SPECIAL_TOKENS.get('<PAD>', 0)
        self.config = NexaConfig(""",
"""        if torch is None:
            raise RuntimeError("PyTorch is not installed.")
            
        self.pad_token_id = DEFAULT_SPECIAL_TOKENS.get('<PAD>', 0)
        self.config = NexaConfig("""
)

open("backend/models/chat_engine.py", "w").write(content)
