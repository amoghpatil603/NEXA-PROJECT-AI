from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

class DatasetStatus(Enum):
    NOT_DOWNLOADED = "NOT_DOWNLOADED"
    DOWNLOADED = "DOWNLOADED"
    VERIFIED = "VERIFIED"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"

@dataclass
class DatasetRecord:
    dataset_id: str
    display_name: str
    description: str
    purpose: str
    license: str
    languages: List[str]
    version: str
    expected_size: int
    local_storage_path: str
    primary_source: str
    mirror_sources: List[str] = field(default_factory=list)
    checksum: Optional[str] = None
    status: DatasetStatus = DatasetStatus.NOT_DOWNLOADED

    def to_dict(self):
        return {
            "dataset_id": self.dataset_id,
            "display_name": self.display_name,
            "description": self.description,
            "purpose": self.purpose,
            "license": self.license,
            "languages": self.languages,
            "version": self.version,
            "expected_size": self.expected_size,
            "local_storage_path": self.local_storage_path,
            "primary_source": self.primary_source,
            "mirror_sources": self.mirror_sources,
            "checksum": self.checksum,
            "status": self.status.value
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            dataset_id=data["dataset_id"],
            display_name=data["display_name"],
            description=data["description"],
            purpose=data["purpose"],
            license=data["license"],
            languages=data["languages"],
            version=data["version"],
            expected_size=data.get("expected_size", 0),
            local_storage_path=data["local_storage_path"],
            primary_source=data["primary_source"],
            mirror_sources=data.get("mirror_sources", []),
            checksum=data.get("checksum"),
            status=DatasetStatus(data.get("status", DatasetStatus.NOT_DOWNLOADED.value))
        )
