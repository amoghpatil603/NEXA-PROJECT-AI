import os
import shutil

class BaseTool:
    def __init__(self, name, description, permission_level="Safe"):
        self.name = name
        self.description = description
        self.permission_level = permission_level

class ReadFileTool(BaseTool):
    def __init__(self):
        super().__init__("read_file", "Read a file from the filesystem", "Safe")

    def execute(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

class WriteFileTool(BaseTool):
    def __init__(self):
        super().__init__("write_file", "Write content to a file", "Confirmation Required")

    def execute(self, path, content):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
