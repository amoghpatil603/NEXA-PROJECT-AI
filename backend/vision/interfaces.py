from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
import re

class ModalityType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"

@dataclass
class ImageInput:
    mime_type: str
    payload_ref: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.mime_type, str) or not re.match(r"^image/[a-zA-Z0-9.+-]+$", self.mime_type):
            raise ValueError(f"Invalid image mime type: '{self.mime_type}'")
        if not isinstance(self.payload_ref, str) or not self.payload_ref.strip():
            raise ValueError("payload_ref must be a non-empty string reference")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")

@dataclass
class AudioInput:
    mime_type: str
    payload_ref: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.mime_type, str) or not re.match(r"^audio/[a-zA-Z0-9.+-]+$", self.mime_type):
            raise ValueError(f"Invalid audio mime type: '{self.mime_type}'")
        if not isinstance(self.payload_ref, str) or not self.payload_ref.strip():
            raise ValueError("payload_ref must be a non-empty string reference")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")

@dataclass
class MultimodalRequest:
    prompt: str
    images: List[ImageInput] = field(default_factory=list)
    audios: List[AudioInput] = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.prompt, str) or not self.prompt.strip():
            raise ValueError("prompt must be a non-empty string")
        if not isinstance(self.images, list):
            raise ValueError("images must be a list of ImageInput")
        if not isinstance(self.audios, list):
            raise ValueError("audios must be a list of AudioInput")
        for img in self.images:
            if not isinstance(img, ImageInput):
                raise ValueError("All image inputs must be ImageInput instances")
        for aud in self.audios:
            if not isinstance(aud, AudioInput):
                raise ValueError("All audio inputs must be AudioInput instances")
