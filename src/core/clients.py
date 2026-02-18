"""외부 AI 클라이언트 추상화.

Anthropic / OpenAI를 통일된 인터페이스로 제공합니다.
AI_PROVIDER 설정에 따라 적절한 클라이언트를 사용합니다.
"""

from __future__ import annotations

from dataclasses import dataclass

import anthropic
import openai

from src.core.config import settings


# ── 통일 응답 모델 ────────────────────────────────────────────


@dataclass
class AIResponse:
    """프로바이더에 독립적인 AI 응답."""

    content: str
    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


# ── 싱글턴 클라이언트 ─────────────────────────────────────────

_anthropic_client: anthropic.AsyncAnthropic | None = None
_openai_client: openai.AsyncOpenAI | None = None


def _get_anthropic_client() -> anthropic.AsyncAnthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key,
        )
    return _anthropic_client


def _get_openai_client() -> openai.AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = openai.AsyncOpenAI(
            api_key=settings.openai_api_key,
        )
    return _openai_client


def reset_client() -> None:
    """클라이언트 초기화 (설정 변경 시 호출)."""
    global _anthropic_client, _openai_client
    _anthropic_client = None
    _openai_client = None


# ── 통일 메시지 생성 API ──────────────────────────────────────


async def create_message(
    *,
    system: str,
    user_message: str,
    model: str | None = None,
    max_tokens: int | None = None,
    provider: str | None = None,
) -> AIResponse:
    """프로바이더에 독립적인 메시지 생성.

    Args:
        system: 시스템 프롬프트
        user_message: 사용자 메시지
        model: 모델 이름 (None이면 설정에서 가져옴)
        max_tokens: 최대 토큰 수 (None이면 설정에서 가져옴)
        provider: 프로바이더 강제 지정 (None이면 설정에서 가져옴)
    """
    active_provider = provider or settings.ai_provider

    if active_provider == "openai":
        return await _create_openai_message(
            system=system,
            user_message=user_message,
            model=model or settings.openai_model,
            max_tokens=max_tokens or settings.openai_max_tokens,
        )
    else:
        return await _create_anthropic_message(
            system=system,
            user_message=user_message,
            model=model or settings.model,
            max_tokens=max_tokens or settings.max_tokens,
        )


async def _create_anthropic_message(
    *,
    system: str,
    user_message: str,
    model: str,
    max_tokens: int,
) -> AIResponse:
    """Anthropic Claude API 호출."""
    client = _get_anthropic_client()
    response = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )

    if not response.content or not hasattr(response.content[0], "text"):
        raise ValueError("API 응답에 텍스트 콘텐츠가 없습니다")

    return AIResponse(
        content=response.content[0].text,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )


async def _create_openai_message(
    *,
    system: str,
    user_message: str,
    model: str,
    max_tokens: int,
) -> AIResponse:
    """OpenAI Responses API 호출."""
    client = _get_openai_client()
    response = await client.responses.create(
        model=model,
        max_output_tokens=max_tokens,
        instructions=system,
        input=user_message,
    )

    if not response.output_text:
        raise ValueError("API 응답에 텍스트 콘텐츠가 없습니다")

    usage = response.usage
    return AIResponse(
        content=response.output_text,
        input_tokens=usage.input_tokens if usage else 0,
        output_tokens=usage.output_tokens if usage else 0,
    )


# ── 하위 호환 ─────────────────────────────────────────────────


def get_async_client() -> anthropic.AsyncAnthropic:
    """[Deprecated] Anthropic 전용 클라이언트. create_message() 사용을 권장."""
    return _get_anthropic_client()
