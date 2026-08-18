import os
import sys
import json

# Setup some fake data in memory and RAG
from execution_engine import ExecutionEngine

def test():
    engine = ExecutionEngine()
    engine.memory_engine.create_memory("user_fact", "User likes apples")
    
    # Try testing the process_request
    context = engine.process_request("Do you know what I like?")
    print(json.dumps(context, indent=2))

if __name__ == "__main__":
    test()
