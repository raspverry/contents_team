"""마크다운 → JSON 렌더링 어댑터.

에이전트가 출력한 마크다운을 content.json 구조로 변환합니다.
레이아웃 디자이너의 출력에서 JSON 블록을 추출하거나,
일반 마크다운을 카드 슬라이드 구조로 변환합니다.
"""

from __future__ import annotations

import json
import re


def extract_json_from_markdown(md: str) -> dict | None:
    """마크다운 내 JSON 코드블록에서 content.json을 추출.

    레이아웃 디자이너가 ```json ... ``` 블록으로 출력한 경우를 처리합니다.
    """
    # JSON 코드블록 찾기
    pattern = r"```(?:json)?\s*\n(\{[\s\S]*?\})\s*\n```"
    matches = re.findall(pattern, md)
    for match in matches:
        try:
            data = json.loads(match)
            if "cards" in data:
                return data
        except json.JSONDecodeError:
            continue
    return None


def markdown_to_cards(md: str, *, theme_id: str = "") -> dict:
    """일반 마크다운을 카드뉴스 content.json 구조로 변환.

    H1 → 커버, H2 → 본문 카드, 마지막 → CTA.
    TIP/주의 등의 블록인용 → highlight-box.
    """
    # 먼저 JSON 블록이 있으면 그대로 사용
    extracted = extract_json_from_markdown(md)
    if extracted:
        return extracted

    cards: list[dict] = []
    page = 1

    # 라인별 파싱
    lines = md.strip().split("\n")
    current_title = ""
    current_body_lines: list[str] = []
    cover_done = False

    def _flush_card() -> None:
        nonlocal page, current_title, current_body_lines, cover_done
        if not current_title and not current_body_lines:
            return

        body_text = "\n".join(current_body_lines).strip()

        # highlight-box 추출
        blocks: list[dict] = []
        highlight_match = re.search(
            r"(?:>\s*\*\*?(TIP|주의|참고|핵심)\*\*?[:\s]*(.+?)(?:\n|$))",
            body_text,
            re.IGNORECASE,
        )

        if not cover_done:
            blocks.append({
                "type": "cover",
                "data": {"title": current_title, "subtitle": body_text[:80] if body_text else ""},
            })
            cards.append({"page": page, "frame": "cover", "blocks": blocks})
            cover_done = True
        else:
            clean_body = body_text
            if highlight_match:
                clean_body = body_text[:highlight_match.start()].strip()

            blocks.append({
                "type": "body-text",
                "data": {"title": current_title, "body": clean_body},
            })
            if highlight_match:
                blocks.append({
                    "type": "highlight-box",
                    "data": {"label": highlight_match.group(1), "text": highlight_match.group(2).strip()},
                })
            cards.append({"page": page, "frame": "body", "blocks": blocks})

        page += 1
        current_title = ""
        current_body_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("## "):
            _flush_card()
            current_title = stripped[2:].strip()
        elif stripped.startswith("## "):
            _flush_card()
            current_title = stripped[3:].strip()
        else:
            if stripped:
                current_body_lines.append(stripped)

    _flush_card()

    # CTA 카드 추가
    cards.append({
        "page": page,
        "frame": "cta",
        "blocks": [{"type": "cta", "data": {"text": "팔로우하고 더 많은 재테크 팁 받기"}}],
    })

    return {"cards": cards}
