"""Abstract uploader interface. Real OAuth/API implementations are deliberately
deferred to Phase 8.4 — until then every uploader raises NotImplementedError so
the pipeline falls back to "generate files locally" (see generator/upload/run.py)."""

from abc import ABC, abstractmethod
from pathlib import Path


class Uploader(ABC):
    @abstractmethod
    def upload(self, video_path: Path, metadata_path: Path) -> None:
        ...


class TikTokUploader(Uploader):
    def upload(self, video_path: Path, metadata_path: Path) -> None:
        raise NotImplementedError("TikTok upload not implemented yet — see Phase 8.4")


class YouTubeUploader(Uploader):
    def upload(self, video_path: Path, metadata_path: Path) -> None:
        raise NotImplementedError("YouTube upload not implemented yet — see Phase 8.4")


class FacebookUploader(Uploader):
    def upload(self, video_path: Path, metadata_path: Path) -> None:
        raise NotImplementedError("Facebook upload not implemented yet — see Phase 8.4")


_UPLOADERS: dict[str, type[Uploader]] = {
    "tiktok": TikTokUploader,
    "youtube": YouTubeUploader,
    "facebook": FacebookUploader,
}


def get_uploader(name: str) -> Uploader:
    try:
        cls = _UPLOADERS[name]
    except KeyError:
        raise ValueError(f"Unknown uploader: {name!r}. Available: {list(_UPLOADERS)}")
    return cls()
