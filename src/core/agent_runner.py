"""에이전트 실행 엔진.

Anthropic API를 호출하여 에이전트를 실행하고 결과를 반환합니다.
"""

from __future__ import annotations

from datetime import datetime, date
from pathlib import Path

import anthropic

from src.core.config import settings, OUTPUTS_DIR
from src.core.models import AgentInfo, AgentRunResult, AgentRunStatus


# 팀별 출력 디렉토리 매핑
TEAM_OUTPUT_DIR = {
    "team1-branding": "branding",
    "team2-analysis": "analysis",
    "team3-reels": "reels",
    "team4-threads": "threads",
    "team5-fanding": "fanding",
}


def _get_output_path(agent: AgentInfo, suffix: str = "") -> Path:
    """에이전트 결과물 저장 경로 생성."""
    subdir = TEAM_OUTPUT_DIR.get(agent.team.value, "misc")
    output_dir = OUTPUTS_DIR / subdir
    output_dir.mkdir(parents=True, exist_ok=True)

    today = date.today().isoformat()
    filename = f"{today}-{agent.id}"
    if suffix:
        filename += f"-{suffix}"
    filename += ".md"

    return output_dir / filename


def run_agent(
    agent: AgentInfo,
    user_message: str,
    context: str = "",
    save_output: bool = True,
) -> AgentRunResult:
    """에이전트를 실행하고 결과를 반환합니다.

    Args:
        agent: 실행할 에이전트 정보
        user_message: 사용자 요청 메시지
        context: 이전 에이전트 결과 등 추가 컨텍스트
        save_output: 결과를 파일로 저장할지 여부
    """
    result = AgentRunResult(
        agent_id=agent.id,
        status=AgentRunStatus.RUNNING,
    )

    # 시스템 프롬프트 조합
    system = agent.system_prompt
    if context:
        system += f"\n\n## 참고 컨텍스트\n{context}"

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model=settings.model,
            max_tokens=settings.max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )

        content = response.content[0].text
        tokens = response.usage.input_tokens + response.usage.output_tokens

        result.status = AgentRunStatus.COMPLETED
        result.content = content
        result.tokens_used = tokens
        result.finished_at = datetime.now()

        # 결과물 파일 저장
        if save_output:
            output_path = _get_output_path(agent)
            output_path.write_text(
                f"# {agent.name} — {date.today().isoformat()}\n\n{content}",
                encoding="utf-8",
            )
            result.output_file = str(output_path)

    except anthropic.APIError as e:
        result.status = AgentRunStatus.FAILED
        result.error = str(e)
        result.finished_at = datetime.now()

    return result


async def run_agent_async(
    agent: AgentInfo,
    user_message: str,
    context: str = "",
    save_output: bool = True,
) -> AgentRunResult:
    """에이전트를 비동기로 실행합니다."""
    result = AgentRunResult(
        agent_id=agent.id,
        status=AgentRunStatus.RUNNING,
    )

    system = agent.system_prompt
    if context:
        system += f"\n\n## 참고 컨텍스트\n{context}"

    try:
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        response = await client.messages.create(
            model=settings.model,
            max_tokens=settings.max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )

        content = response.content[0].text
        tokens = response.usage.input_tokens + response.usage.output_tokens

        result.status = AgentRunStatus.COMPLETED
        result.content = content
        result.tokens_used = tokens
        result.finished_at = datetime.now()

        if save_output:
            output_path = _get_output_path(agent)
            output_path.write_text(
                f"# {agent.name} — {date.today().isoformat()}\n\n{content}",
                encoding="utf-8",
            )
            result.output_file = str(output_path)

    except anthropic.APIError as e:
        result.status = AgentRunStatus.FAILED
        result.error = str(e)
        result.finished_at = datetime.now()

    return result
