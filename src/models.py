import hashlib
import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class SkatingWindow:
    source_key: str
    title: str
    start: str
    end: str
    location: str
    description: str
    url: str
    activity_id: int
    status: str
    site_name: str
    facility_name: str

    def to_dict(self) -> dict:
        return asdict(self)

    def content_hash(self) -> str:
        payload = {
            "title": self.title,
            "start": self.start,
            "end": self.end,
            "location": self.location,
            "description": self.description,
            "url": self.url,
            "status": self.status,
        }
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
