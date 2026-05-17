import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CALENDAR_NAME = "Patinage Montréal"
DEFAULT_TIME_ZONE = "America/Toronto"


def load_env_file(path: Path | None = None) -> None:
    env_path = path or ROOT_DIR / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def env_path(name: str, default: str) -> Path:
    return resolve_repo_path(os.environ.get(name, default))


def resolve_repo_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = ROOT_DIR / path
    return path


def env_str(name: str, default: str) -> str:
    return os.environ.get(name, default)
