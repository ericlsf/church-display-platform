from dataclasses import dataclass, field
from typing import Any


class ValidationError(ValueError):
    pass


def _required_text(value: Any, name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValidationError(f"{name} is required")
    return text


@dataclass(frozen=True)
class PlaylistRef:
    remote: str
    folder: str

    @classmethod
    def from_mapping(cls, data: dict[str, Any]):
        return cls(
            remote=str(data.get("remote") or "gdrive").strip() or "gdrive",
            folder=_required_text(data.get("folder"), "folder").strip("/"),
        )


@dataclass(frozen=True)
class DeployPayload:
    remote: str
    folder: str
    run_now: bool = True
    playlist_order: list[str] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, data: dict[str, Any]):
        ref = PlaylistRef.from_mapping(data)
        order = []
        seen = set()
        for raw in data.get("playlist_order") or []:
            item = str(raw or "").strip().strip("/")
            if item and item not in seen:
                seen.add(item)
                order.append(item)
        return cls(ref.remote, ref.folder, bool(data.get("run_now", True)), order)


@dataclass(frozen=True)
class HeartbeatPayload:
    display_id: str
    hostname: str
    version: str

    @classmethod
    def from_mapping(cls, data: dict[str, Any]):
        return cls(
            display_id=_required_text(data.get("id"), "id"),
            hostname=_required_text(data.get("hostname"), "hostname"),
            version=str(data.get("version") or "Unknown"),
        )
