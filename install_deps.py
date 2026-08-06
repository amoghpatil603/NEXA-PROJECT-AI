import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Let's see if we can find the right python
import os
print("Executable:", sys.executable)
