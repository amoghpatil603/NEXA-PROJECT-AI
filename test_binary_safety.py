import os
import shutil
import hashlib

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def test_binary_safety():
    # create a dummy bin file
    dummy = b'\x12\x34\xff\xfe\x00\x00'
    with open("test_bin.bin", "wb") as f:
        f.write(dummy)
    
    orig_sha = sha256_file("test_bin.bin")
    
    # Try to rewrite it as text
    try:
        with open("test_bin.bin", "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        with open("test_bin.bin", "w", encoding="utf-8", errors="replace") as f:
            f.write(text)
    except Exception:
        pass
        
    new_sha = sha256_file("test_bin.bin")
    assert orig_sha != new_sha, "Binary rewrite test failed: Hash unchanged after text-mode rewrite!"
    print("Binary safety test PASS: Text-mode rewrite correctly alters the binary hash.")

if __name__ == "__main__":
    test_binary_safety()
