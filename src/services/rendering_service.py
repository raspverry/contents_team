"""렌더링 서비스.

Remotion CLI를 호출하여 카드뉴스(PNG/MP4), 릴스(MP4)를 렌더링합니다.
Node.js + Remotion이 설치된 환경에서만 동작합니다.
"""

from __future__ import annotations

import asyncio
import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

from src.core.config import BASE_DIR, settings


RENDERING_DIR = BASE_DIR / "rendering"
OUTPUT_DIR = BASE_DIR / "outputs"

# 기본 테마 (rendering/src/theme.ts 의 DEFAULT_*_THEME 과 동기)
_DEFAULT_CARDNEWS_THEME = {
    "primary": "#D4AF37",
    "secondary": "#1A1A2E",
    "background": "#FFFFFF",
    "text": "#1A1A2E",
    "accent": "#4ECDC4",
}

_DEFAULT_REELS_THEME = {
    "primary": "#D4AF37",
    "secondary": "#1A1A2E",
    "background": "#0F0F1A",
    "text": "#FFFFFF",
    "accent": "#4ECDC4",
}

# 카드뉴스 테마 프리셋 (rendering/src/theme.ts 의 THEME_PRESETS 와 동기)
THEME_PRESETS: dict[str, dict[str, str]] = {
    "premium-dark": {
        "primary": "#C8A951",
        "secondary": "#0A1628",
        "background": "#121E33",
        "text": "#F0EEE9",
        "accent": "#2EC4B6",
    },
    "trust-blue": {
        "primary": "#1B4DFF",
        "secondary": "#0D1B2A",
        "background": "#FFFFFF",
        "text": "#1A1A2E",
        "accent": "#3B82F6",
    },
    "warm-wealth": {
        "primary": "#A47864",
        "secondary": "#2C1810",
        "background": "#FBF8F4",
        "text": "#2C1810",
        "accent": "#C2703E",
    },
    "emerald-growth": {
        "primary": "#10B981",
        "secondary": "#0B1D1A",
        "background": "#0F2A24",
        "text": "#ECFDF5",
        "accent": "#34D399",
    },
    "neo-contrast": {
        "primary": "#FFE135",
        "secondary": "#1F1F1F",
        "background": "#000000",
        "text": "#FFFFFF",
        "accent": "#FF6B6B",
    },
}


class RenderType(str, Enum):
    CARDNEWS_VIDEO = "CardNews"
    CARDNEWS_STILL = "CardNewsStill"
    REELS = "Reels"


@dataclass
class RenderResult:
    """렌더링 결과."""

    success: bool
    output_path: str = ""
    error: str = ""
    duration_ms: int = 0


def resolve_theme(theme_id: str | None) -> dict[str, str]:
    """테마 ID로 색상 팔레트 조회. 없으면 기본 카드뉴스 테마."""
    if not theme_id:
        return _DEFAULT_CARDNEWS_THEME
    return THEME_PRESETS.get(theme_id, _DEFAULT_CARDNEWS_THEME)


def is_remotion_available() -> bool:
    """Remotion CLI가 사용 가능한지 확인."""
    npx = shutil.which("npx")
    if not npx:
        return False
    node_modules = RENDERING_DIR / "node_modules"
    return node_modules.exists()


def _brand_props() -> dict[str, str]:
    """브랜드 정보를 Remotion props 형태로 반환."""
    return {
        "brandName": settings.brand_name,
        "brandHandle": settings.brand_handle,
    }


async def render_cardnews_stills(
    content_json: dict,
    output_subdir: str = "cardnews",
) -> list[RenderResult]:
    """카드뉴스를 개별 PNG 이미지로 렌더링."""
    results: list[RenderResult] = []
    cards = content_json.get("cards", [])
    theme = content_json.get("theme", _DEFAULT_CARDNEWS_THEME)

    out_dir = OUTPUT_DIR / output_subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    for card in cards:
        page = card.get("page", 0)
        output_path = out_dir / f"card-{timestamp}-p{page}.png"

        props = json.dumps({"card": card, "theme": theme, **_brand_props()})
        result = await _run_remotion_still(
            composition="CardNewsStill",
            props=props,
            output_path=str(output_path),
        )
        results.append(result)

    return results


async def render_cardnews_video(
    content_json: dict,
    output_subdir: str = "cardnews",
) -> RenderResult:
    """카드뉴스를 슬라이드 영상(MP4)으로 렌더링."""
    cards = content_json.get("cards", [])
    theme = content_json.get("theme", _DEFAULT_CARDNEWS_THEME)

    out_dir = OUTPUT_DIR / output_subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = out_dir / f"cardnews-{timestamp}.mp4"

    frames_per_card = 90  # 3초 @ 30fps
    total_frames = len(cards) * frames_per_card

    props = json.dumps({
        "cards": cards,
        "theme": theme,
        **_brand_props(),
    })

    return await _run_remotion_render(
        composition="CardNews",
        props=props,
        output_path=str(output_path),
        duration_frames=total_frames,
    )


async def render_reels(
    scenes: list[dict],
    output_subdir: str = "reels",
    brand_name: str = "",
) -> RenderResult:
    """릴스 영상(MP4)을 렌더링."""
    out_dir = OUTPUT_DIR / output_subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = out_dir / f"reels-{timestamp}.mp4"

    total_seconds = sum(s.get("durationSeconds", 5) for s in scenes)
    total_frames = total_seconds * 30

    props = json.dumps({
        "scenes": scenes,
        "theme": _DEFAULT_REELS_THEME,
        "brandName": brand_name or settings.brand_name,
        "brandHandle": settings.brand_handle,
    })

    return await _run_remotion_render(
        composition="Reels",
        props=props,
        output_path=str(output_path),
        duration_frames=total_frames,
    )


# ── 내부 함수 ──────────────────────────────────────────────


async def _run_remotion_render(
    composition: str,
    props: str,
    output_path: str,
    duration_frames: int,
) -> RenderResult:
    """Remotion render 명령 실행."""
    if not is_remotion_available():
        return RenderResult(
            success=False,
            error="Remotion이 설치되지 않았습니다. rendering/ 디렉토리에서 npm install을 실행하세요.",
        )

    start = datetime.now()
    cmd = [
        "npx", "remotion", "render",
        composition,
        "--output", output_path,
        "--props", props,
        "--frames", f"0-{duration_frames - 1}",
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(RENDERING_DIR),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        elapsed = int((datetime.now() - start).total_seconds() * 1000)

        if proc.returncode == 0:
            return RenderResult(
                success=True,
                output_path=output_path,
                duration_ms=elapsed,
            )
        return RenderResult(
            success=False,
            error=stderr.decode()[:500],
            duration_ms=elapsed,
        )
    except Exception as e:
        elapsed = int((datetime.now() - start).total_seconds() * 1000)
        return RenderResult(
            success=False,
            error=str(e),
            duration_ms=elapsed,
        )


async def _run_remotion_still(
    composition: str,
    props: str,
    output_path: str,
) -> RenderResult:
    """Remotion still 명령 실행 (정지 이미지)."""
    if not is_remotion_available():
        return RenderResult(
            success=False,
            error="Remotion이 설치되지 않았습니다. rendering/ 디렉토리에서 npm install을 실행하세요.",
        )

    start = datetime.now()
    cmd = [
        "npx", "remotion", "still",
        composition,
        "--output", output_path,
        "--props", props,
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(RENDERING_DIR),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        elapsed = int((datetime.now() - start).total_seconds() * 1000)

        if proc.returncode == 0:
            return RenderResult(
                success=True,
                output_path=output_path,
                duration_ms=elapsed,
            )
        return RenderResult(
            success=False,
            error=stderr.decode()[:500],
            duration_ms=elapsed,
        )
    except Exception as e:
        elapsed = int((datetime.now() - start).total_seconds() * 1000)
        return RenderResult(
            success=False,
            error=str(e),
            duration_ms=elapsed,
        )
