"""산출물 서비스.

산출물 목록 조회, 내용 읽기를 담당합니다.
"""

from __future__ import annotations

from src.services.storage import OutputItem, get_storage


def list_outputs(
    team: str | None = None, date_str: str | None = None
) -> list[OutputItem]:
    """산출물 목록 조회."""
    return get_storage().list_outputs(team=team, date_str=date_str)


def get_output_content(team: str, filename: str) -> str | None:
    """산출물 내용 읽기. 없거나 경로 이탈이면 None."""
    return get_storage().load(team, filename)
