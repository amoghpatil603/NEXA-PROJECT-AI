
import os
import shutil
import struct
import hashlib

def test_regression():
    # Write a test to ensure mode 'wb' overwrites instead of appends
    test_path = 'test_shard.bin'
    data = struct.pack('<H', 1)
    
    with open(test_path, 'wb') as f:
        f.write(data)
    with open(test_path, 'wb') as f:
        f.write(data)
        
    assert os.path.getsize(test_path) == 2, "Failed: 'wb' appended data"
    
    with open(test_path, 'ab') as f:
        f.write(data)
        
    assert os.path.getsize(test_path) == 4, "Failed: 'ab' did not append"
    os.remove(test_path)
    return True

if __name__ == '__main__':
    assert test_regression()
