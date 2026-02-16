"""스토리지 추상화 레이어.

파일시스템 기반 구현. SaaS 전환 시 DB/S3 구현으로 교체 가능.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from src.core.config import OUTPUTS_DIR


@dataclass
class OutputItem:
    """저장된 산출물 메타데이터."""

    team: str
    filename: str
    path: str
    size: int
    created_at: datetime


class StorageBackend(ABC):
    """스토리지 인터페이스. DB/S3 전환 시 이 인터페이스만 구현."""

    @abstractmethod
    def save(self, team_dir: str, filename: str, content: str) -> str:
        """콘텐츠를 저장하고 저장 경로를 반환."""

    @abstractmethod
    def load(self, team_dir: str, filename: str) -> str | None:
        """콘텐츠를 로드. 없으면 None."""

    @abstractmethod
    def list_outputs(
        self, team: str | None = None, date_str: str | None = None
    ) -> list[OutputItem]:
        """산출물 목록 조회."""

    @abstractmethod
    def generate_filename(self, agent_id: str, suffix: str = "") -> str:
        """고유한 파일명 생성."""


class FileStorage(StorageBackend):
    """파일시스템 기반 스토리지."""

    def __init__(self, base_dir: Path = OUTPUTS_DIR):
        self._base_dir = base_dir

    def save(self, team_dir: str, filename: str, content: str) -> str:
        output_dir = self._base_dir / team_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / filename
        filepath.write_text(content, encoding="utf-8")
        return str(filepath)

    def load(self, team_dir: str, filename: str) -> str | None:
        filepath = self._base_dir / team_dir / filename
        if not filepath.exists():
            return None
        # path traversal 방지
        resolved = filepath.resolve()
        if not str(resolved).startswith(str(self._base_dir.resolve())):
            return None
        return resolved.read_text(encoding="utf-8")

    def list_outputs(
        self, team: str | None = None, date_str: str | None = None
    ) -> list[OutputItem]:
        items: list[OutputItem] = []
        for subdir in sorted(self._base_dir.iterdir()):
            if not subdir.is_dir():
                continue
            if team and subdir.name != team:
                continue
            for f in sorted(subdir.glob("*.md"), reverse=True):
                if date_str and not f.name.startswith(date_str):
                    continue
                stat = f.stat()
                items.append(
                    OutputItem(
                        team=subdir.name,
                        filename=f.name,
                        path=str(f),
                        size=stat.st_size,
                        created_at=datetime.fromtimestamp(stat.st_mtime),
                    )
                )
        return items

    def generate_filename(self, agent_id: str, suffix: str = "") -> str:
        """고유한 파일명 생성. 같은 에이전트의 같은 날 중복 실행도 안전."""
        today = date.today().isoformat()
        timestamp = datetime.now().strftime("%H%M%S%f")  # 마이크로초 포함
        parts = [today, agent_id, timestamp]
        if suffix:
            parts.append(suffix)
        return "-".join(parts) + ".md"


# 기본 스토리지 인스턴스
_storage: StorageBackend | None = None


def get_storage() -> StorageBackend:
    """스토리지 싱글턴 반환."""
    global _storage
    if _storage is None:
        _storage = FileStorage()
    return _storage
