"""에이전트 프롬프트 파일 로더.

agents/ 디렉토리의 마크다운 파일에서 에이전트 정보를 파싱합니다.
"""

from __future__ import annotations

import re
from pathlib import Path

from src.core.config import AGENTS_DIR
from src.core.models import AgentInfo, TeamType


def _extract_between(text: str, start_marker: str, end_marker: str) -> str:
    """두 마커 사이의 텍스트를 추출."""
    pattern = re.escape(start_marker) + r"(.*?)" + re.escape(end_marker)
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""


def _extract_table_value(text: str, key: str) -> str:
    """마크다운 테이블에서 특정 키의 값을 추출."""
    pattern = rf"\*\*{re.escape(key)}\*\*\s*\|\s*(.+)"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""


def _extract_heading_title(text: str) -> str:
    """첫 번째 H1에서 한글 이름 추출. 예: '# 트렌드 헌터 (Trend Hunter)' → '트렌드 헌터'"""
    match = re.search(r"^#\s+(.+)", text, re.MULTILINE)
    if not match:
        return ""
    title = match.group(1).strip()
    # 괄호 앞의 한글 이름만 추출
    paren_match = re.match(r"(.+?)\s*\(", title)
    return paren_match.group(1).strip() if paren_match else title


def parse_agent_file(filepath: Path) -> AgentInfo | None:
    """에이전트 마크다운 파일을 파싱하여 AgentInfo 반환."""
    text = filepath.read_text(encoding="utf-8")

    # 팀 타입 결정 (부모 디렉토리명)
    team_dir = filepath.parent.name
    try:
        team = TeamType(team_dir)
    except ValueError:
        return None

    # 시스템 프롬프트 추출 (``` 블록)
    system_prompt = _extract_between(text, "## 시스템 프롬프트\n\n```", "```")
    if not system_prompt:
        # 대체: 첫 번째 ``` 블록
        match = re.search(
            r"## 시스템 프롬프트\s*\n+```\w*\n(.*?)```", text, re.DOTALL
        )
        if match:
            system_prompt = match.group(1).strip()

    return AgentInfo(
        id=filepath.stem,
        name=_extract_heading_title(text),
        team=team,
        role=_extract_table_value(text, "역할"),
        frequency=_extract_table_value(text, "실행 빈도"),
        system_prompt=system_prompt,
        source_file=str(filepath.relative_to(AGENTS_DIR.parent)),
    )


def load_all_agents() -> dict[str, AgentInfo]:
    """모든 에이전트 정보를 로드하여 {agent_id: AgentInfo} 딕셔너리 반환."""
    agents: dict[str, AgentInfo] = {}

    for team_dir in sorted(AGENTS_DIR.iterdir()):
        if not team_dir.is_dir():
            continue
        for md_file in sorted(team_dir.glob("*.md")):
            agent = parse_agent_file(md_file)
            if agent:
                agents[agent.id] = agent

    return agents
