import urllib.request
import os

url = "https://bootstrap.pypa.io/get-pip.py"
urllib.request.urlretrieve(url, "get-pip.py")
os.system("python3 get-pip.py")
os.system("python3 -m pip install numpy sentence-transformers pypdf python-docx --no-cache-dir")
