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

