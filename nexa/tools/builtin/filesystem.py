import os
from ..registry import NexaTool, ToolRegistry

@ToolRegistry.register
class FileReader(NexaTool):
    name = "file_reader"
    description = "Reads the content of a local file."
    arguments = {"path": "Path to the file to read"}
    requires_permission = False

    def execute(self, path: str):
        try:
            if not os.path.exists(path):
                return f"Error: File {path} not found."
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error: {str(e)}"

@ToolRegistry.register
class FileWriter(NexaTool):
    name = "file_writer"
    description = "Writes content to a local file. REQUIRES PERMISSION."
    arguments = {"path": "Target file path", "content": "Content to write"}
    requires_permission = True

    def execute(self, path: str, content: str):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error: {str(e)}"

@ToolRegistry.register
class FolderSearch(NexaTool):
    name = "folder_search"
    description = "Lists files in a directory."
    arguments = {"path": "Directory path to search"}
    requires_permission = False

    def execute(self, path: str):
        try:
            if not os.path.isdir(path):
                return f"Error: {path} is not a directory."
            return os.listdir(path)
        except Exception as e:
            return f"Error: {str(e)}"
