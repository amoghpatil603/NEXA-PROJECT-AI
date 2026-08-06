import sys
content = open("backend/models/chat_engine.py").read()

content = content.replace("logits: torch.Tensor", "logits: 'Any'")
content = content.replace("from typing import Optional, List, Dict, Generator, Tuple", "from typing import Optional, List, Dict, Generator, Tuple, Any")

open("backend/models/chat_engine.py", "w").write(content)
