"""에이전트 서비스.

에이전트 로딩(캐시), 실행, 결과 저장을 담당하는 서비스 레이어.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from pathlib import Path

import anthropic
import openai

from src.core.clients import create_message
from src.core.config import AGENTS_DIR, settings
from src.core.models import AgentInfo, AgentRunResult, RunStatus, TeamType, get_language_profile, inject_language_guide
from src.services.storage import get_storage


# ── 에이전트 로딩 (캐시) ─────────────────────────────────────


_agent_cache: dict[str, AgentInfo] | None = None


def _substitute_brand_vars(text: str) -> str:
    """프롬프트 내 {{변수}}를 settings 값으로 치환."""
    lang = get_language_profile(settings.content_language)
    replacements = {
        "{{brand_name}}": settings.brand_name,
        "{{brand_handle}}": settings.brand_handle,
        "{{brand_topic}}": settings.brand_topic,
        "{{brand_description}}": settings.brand_description,
        "{{brand_disclaimer}}": settings.brand_disclaimer,
        "{{content_language}}": lang.label,
        "{{language_instruction}}": lang.instruction,
        "{{language_style_guide}}": lang.style_guide,
    }
    for key, val in replacements.items():
        text = text.replace(key, val)
    return text


def _parse_agent_file(filepath: Path) -> AgentInfo | None:
    """에이전트 마크다운 파일을 파싱하여 AgentInfo 반환."""
    text = filepath.read_text(encoding="utf-8")

    team_dir = filepath.parent.name
    try:
        team = TeamType(team_dir)
    except ValueError:
        return None

    # H1에서 한글 이름 추출
    h1 = re.search(r"^#\s+(.+)", text, re.MULTILINE)
    if not h1:
        return None
    title = h1.group(1).strip()
    paren = re.match(r"(.+?)\s*\(", title)
    name = paren.group(1).strip() if paren else title

    # 테이블에서 역할, 빈도 추출
    def table_val(key: str) -> str:
        m = re.search(rf"\*\*{re.escape(key)}\*\*\s*\|\s*(.+)", text)
        return m.group(1).strip() if m else ""

    # 시스템 프롬프트 추출
    prompt_match = re.search(
        r"## 시스템 프롬프트\s*\n+```\w*\n(.*?)```", text, re.DOTALL
    )
    raw_prompt = prompt_match.group(1).strip() if prompt_match else ""
    system_prompt = _substitute_brand_vars(raw_prompt)

    return AgentInfo(
        id=filepath.stem,
        name=name,
        team=team,
        role=table_val("역할"),
        frequency=table_val("실행 빈도"),
        system_prompt=system_prompt,
        source_file=str(filepath.relative_to(AGENTS_DIR.parent)),
    )


def load_all_agents(*, force_reload: bool = False) -> dict[str, AgentInfo]:
    """모든 에이전트를 로드 (캐시 사용)."""
    global _agent_cache
    if _agent_cache is not None and not force_reload:
        return _agent_cache

    agents: dict[str, AgentInfo] = {}
    for team_dir in sorted(AGENTS_DIR.iterdir()):
        if not team_dir.is_dir():
            continue
        for md_file in sorted(team_dir.glob("*.md")):
            agent = _parse_agent_file(md_file)
            if agent:
                agents[agent.id] = agent

    _agent_cache = agents
    return agents


def get_agent(agent_id: str) -> AgentInfo | None:
    """특정 에이전트 조회."""
    return load_all_agents().get(agent_id)


# ── 에이전트 실행 ────────────────────────────────────────────


async def run_agent(
    agent: AgentInfo,
    user_message: str,
    *,
    context: str = "",
    save_output: bool = True,
) -> AgentRunResult:
    """에이전트를 비동기로 실행하고 결과를 반환.

    Args:
        agent: 실행할 에이전트 정보
        user_message: 사용자 요청 메시지
        context: 이전 에이전트 결과 등 추가 컨텍스트
        save_output: 결과를 파일로 저장할지 여부
    """
    run_id = uuid.uuid4().hex[:12]
    result = AgentRunResult(
        run_id=run_id,
        agent_id=agent.id,
        status=RunStatus.RUNNING,
    )

    # 시스템 프롬프트 조합
    system = inject_language_guide(agent.system_prompt, settings.content_language)
    if context:
        system += f"\n\n## 참고 컨텍스트\n{context}"

    try:
        ai_response = await create_message(
            system=system,
            user_message=user_message,
        )

        result.status = RunStatus.COMPLETED
        result.content = ai_response.content
        result.tokens_used = ai_response.total_tokens
        result.finished_at = datetime.now()

        if save_output:
            storage = get_storage()
            filename = storage.generate_filename(agent.id)
            header = f"# {agent.name} — {datetime.now().isoformat()}\n\n"
            saved_path = storage.save(
                agent.team.output_dir, filename, header + ai_response.content
            )
            result.output_file = saved_path

    except (anthropic.APIError, openai.APIError) as e:
        result.status = RunStatus.FAILED
        result.error = str(e)
        result.finished_at = datetime.now()
    except Exception as e:
        result.status = RunStatus.FAILED
        result.error = f"예기치 않은 오류: {e}"
        result.finished_at = datetime.now()

    return result
