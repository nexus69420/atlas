"""Local filesystem storage for uploaded datasets.

Why local disk for V1:
- Zero extra infra (MinIO/S3 can wait until multi-node needs it)
- Same storage interface — swap the backend later without changing services
"""

from pathlib import Path
from uuid import UUID

from app.core.config import get_settings


class LocalStorage:
    """Save/load/delete files under a configurable root directory."""

    def __init__(self, root: Path | None = None) -> None:
        settings = get_settings()
        self._root = root if root is not None else Path(settings.storage_path)
        self._root.mkdir(parents=True, exist_ok=True)

    def build_key(self, project_id: UUID, dataset_id: UUID, extension: str) -> str:
        """Return a relative storage key (portable across machines)."""
        ext = extension if extension.startswith(".") else f".{extension}"
        return f"{project_id}/{dataset_id}{ext}"

    def absolute_path(self, storage_key: str) -> Path:
        path = (self._root / storage_key).resolve()
        # Prevent path traversal outside the storage root
        if not str(path).startswith(str(self._root.resolve())):
            raise ValueError("Invalid storage key")
        return path

    def save(self, storage_key: str, data: bytes) -> Path:
        path = self.absolute_path(storage_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def read_bytes(self, storage_key: str) -> bytes:
        return self.absolute_path(storage_key).read_bytes()

    def delete(self, storage_key: str) -> None:
        path = self.absolute_path(storage_key)
        if path.exists():
            path.unlink()
