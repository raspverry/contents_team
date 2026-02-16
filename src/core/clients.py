"""외부 클라이언트 싱글턴.

Anthropic API 클라이언트를 앱 생애주기 동안 재사용합니다.
"""

from __future__ import annotations

import anthropic

from src.core.config import settings

_async_client: anthropic.AsyncAnthropic | None = None


def get_async_client() -> anthropic.AsyncAnthropic:
    """AsyncAnthropic 클라이언트 싱글턴 반환."""
    global _async_client
    if _async_client is None:
        _async_client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key,
        )
    return _async_client


def reset_client() -> None:
    """클라이언트 초기화 (설정 변경 시 호출)."""
    global _async_client
    _async_client = None
