import hashlib
import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class SkatingWindow:
    source_key: str
    kind: str
    importance: str
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
            "kind": self.kind,
            "importance": self.importance,
            "start": self.start,
            "end": self.end,
            "location": self.location,
            "description": self.description,
            "url": self.url,
            "status": self.status,
        }
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SkatingActivity:
    source_key: str
    kind: str
    importance: str
    title: str
    start_date: str
    end_date: str
    site_name: str
    status: str
    url: str
    activity_id: int
    has_timed_schedules: bool

    def to_dict(self) -> dict:
        return asdict(self)
