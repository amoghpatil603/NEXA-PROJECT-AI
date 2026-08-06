import os
import re
from pathlib import Path
import logging
from typing import Dict, Any, Tuple, List, Optional

logger = logging.getLogger("nexa.security.validation")

# Allowed MIME types and extensions for file uploads
ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif",
    "application/pdf", "text/plain", "text/markdown", "application/json", "text/csv"
}

ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".gif",
    ".pdf", ".txt", ".md", ".json", ".csv"
}

DISALLOWED_EXTENSIONS = {
    ".exe", ".sh", ".bat", ".cmd", ".py", ".js", ".php", ".pl", ".dll", ".so", ".elf",
    ".html", ".htm", ".svg", ".vbs", ".ps1", ".jar", ".war", ".cgi"
}

MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB
MAX_MESSAGE_LENGTH = 10000
MAX_SYSTEM_PROMPT_LENGTH = 4000
MAX_HISTORY_ITEMS = 50

# Threat detection patterns
SUSPICIOUS_PATTERNS = [
    r"ignore\s+previous\s+instructions",
    r"system\s+override",
    r"\.\./\.\./",
    r"rm\s+-rf",
    r"drop\s+table",
    r"<script\b",
    r"exec\s*\("
]

class RequestValidationError(Exception):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

def sanitize_filename(filename: str) -> str:
    """Sanitizes a filename to prevent path traversal and arbitrary code execution."""
    if not filename:
        return "unnamed_file.dat"
    
    # Strip any directory components
    base_name = os.path.basename(filename)
    
    # Remove null bytes and control chars
    base_name = re.sub(r'[\x00-\x1f\x7f]', '', base_name)
    
    # Extract extension safely
    name_part, ext = os.path.splitext(base_name)
    ext = ext.lower()
    
    # Replace unsafe non-alphanumeric characters in name part
    clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', name_part)
    if not clean_name:
        clean_name = "file"
        
    if ext in DISALLOWED_EXTENSIONS:
        ext = ".txt"
    elif ext not in ALLOWED_EXTENSIONS:
        ext = ".dat"
        
    # Enforce safe length limit for filename
    clean_name = clean_name[:64]
    return f"{clean_name}{ext}"

def validate_chat_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validates parameters for the /chat and /chat/stream endpoints."""
    if not isinstance(data, dict):
        raise RequestValidationError("Request body must be a valid JSON object.")
    
    message = data.get("message")
    if not message or not isinstance(message, str):
        raise RequestValidationError("Field 'message' is required and must be a non-empty string.")
    
    if len(message.strip()) == 0:
        raise RequestValidationError("Field 'message' cannot be blank.")
        
    if len(message) > MAX_MESSAGE_LENGTH:
        raise RequestValidationError(f"Field 'message' exceeds maximum allowed length of {MAX_MESSAGE_LENGTH} characters.")
    
    system_prompt = data.get("system_prompt")
    if system_prompt is not None:
        if not isinstance(system_prompt, str):
            raise RequestValidationError("Field 'system_prompt' must be a string.")
        if len(system_prompt) > MAX_SYSTEM_PROMPT_LENGTH:
            raise RequestValidationError(f"Field 'system_prompt' exceeds maximum length of {MAX_SYSTEM_PROMPT_LENGTH} characters.")
            
    history = data.get("history")
    if history is not None:
        if not isinstance(history, list):
            raise RequestValidationError("Field 'history' must be a list of message objects.")
        if len(history) > MAX_HISTORY_ITEMS:
            data["history"] = history[-MAX_HISTORY_ITEMS:]
        for idx, item in enumerate(data.get("history", [])):
            if not isinstance(item, dict):
                raise RequestValidationError(f"History item at index {idx} must be a dictionary.")
            if "content" in item and not isinstance(item["content"], str):
                raise RequestValidationError(f"History item content at index {idx} must be a string.")
                
    max_tokens = data.get("max_tokens")
    if max_tokens is not None:
        try:
            val = int(max_tokens)
            if val < 1 or val > 2048:
                data["max_tokens"] = max(1, min(val, 2048))
        except (ValueError, TypeError):
            data["max_tokens"] = 64
            
    temperature = data.get("temperature")
    if temperature is not None:
        try:
            val = float(temperature)
            data["temperature"] = max(0.0, min(val, 2.0))
        except (ValueError, TypeError):
            data["temperature"] = 0.7
            
    # Check for prompt threats
    threat = scan_for_threats(message)
    if threat["threat_detected"]:
        logger.warning(f"Threat detected in prompt: {threat}")
        
    return data

def validate_file_upload(filename: str, content_type: str, file_size: int) -> Tuple[bool, str]:
    """Validates uploaded file against size, MIME type, and extension restrictions."""
    if file_size > MAX_FILE_SIZE_BYTES:
        return False, f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_BYTES // (1024*1024)}MB."
        
    _, ext = os.path.splitext(filename.lower())
    if ext in DISALLOWED_EXTENSIONS:
        return False, f"File extension '{ext}' is forbidden for security reasons."
        
    if ext not in ALLOWED_EXTENSIONS and content_type not in ALLOWED_MIME_TYPES:
        return False, f"Unsupported file type '{content_type}' or extension '{ext}'."
        
    return True, "Valid"

def scan_for_threats(text: str) -> Dict[str, Any]:
    """Scans input text for known prompt injection / malicious execution patterns."""
    if not text or not isinstance(text, str):
        return {"threat_detected": False}
        
    text_lower = text.lower()
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, text_lower):
            return {
                "threat_detected": True,
                "pattern": pattern,
                "action": "FLAGGED"
            }
            
    return {"threat_detected": False}
