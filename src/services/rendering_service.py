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


def is_remotion_available() -> bool:
    """Remotion CLI가 사용 가능한지 확인."""
    npx = shutil.which("npx")
    if not npx:
        return False
    node_modules = RENDERING_DIR / "node_modules"
    return node_modules.exists()


async def render_cardnews_stills(
    content_json: dict,
    output_subdir: str = "cardnews",
) -> list[RenderResult]:
    """카드뉴스를 개별 PNG 이미지로 렌더링.

    Args:
        content_json: 레이아웃 디자이너의 content.json 출력
        output_subdir: 출력 디렉토리 (outputs/ 하위)

    Returns:
        카드별 RenderResult 리스트
    """
    results: list[RenderResult] = []
    cards = content_json.get("cards", [])
    theme = content_json.get("theme", {
        "primary": "#D4AF37",
        "secondary": "#1A1A2E",
        "background": "#FFFFFF",
        "text": "#1A1A2E",
        "accent": "#4ECDC4",
    })

    out_dir = OUTPUT_DIR / output_subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    for card in cards:
        page = card.get("page", 0)
        output_path = out_dir / f"card-{timestamp}-p{page}.png"

        props = json.dumps({"card": card, "theme": theme})
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
    """카드뉴스를 슬라이드 영상(MP4)으로 렌더링.

    Args:
        content_json: 레이아웃 디자이너의 content.json 출력
        output_subdir: 출력 디렉토리

    Returns:
        RenderResult
    """
    cards = content_json.get("cards", [])
    theme = content_json.get("theme", {
        "primary": "#D4AF37",
        "secondary": "#1A1A2E",
        "background": "#FFFFFF",
        "text": "#1A1A2E",
        "accent": "#4ECDC4",
    })

    out_dir = OUTPUT_DIR / output_subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = out_dir / f"cardnews-{timestamp}.mp4"

    frames_per_card = 90  # 3초 @ 30fps
    total_frames = len(cards) * frames_per_card

    props = json.dumps({"cards": cards, "theme": theme})

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
    """릴스 영상(MP4)을 렌더링.

    Args:
        scenes: 씬 리스트 [{"type": "hook|body|cta", "text": "...", "durationSeconds": 5}]
        output_subdir: 출력 디렉토리
        brand_name: 브랜드명

    Returns:
        RenderResult
    """
    theme = {
        "primary": "#D4AF37",
        "secondary": "#1A1A2E",
        "background": "#0F0F1A",
        "text": "#FFFFFF",
        "accent": "#4ECDC4",
    }

    out_dir = OUTPUT_DIR / output_subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = out_dir / f"reels-{timestamp}.mp4"

    total_seconds = sum(s.get("durationSeconds", 5) for s in scenes)
    total_frames = total_seconds * 30

    props = json.dumps({
        "scenes": scenes,
        "theme": theme,
        "brandName": brand_name or settings.brand_name,
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
