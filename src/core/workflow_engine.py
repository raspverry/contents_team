"""워크플로우 오케스트레이션 엔진.

에이전트 간 의존성을 관리하고, 순차/병렬 실행을 오케스트레이션합니다.
"""

from __future__ import annotations

import asyncio
from datetime import date

from src.core.agent_loader import load_all_agents
from src.core.agent_runner import run_agent_async
from src.core.models import (
    AgentRunResult,
    AgentRunStatus,
    Workflow,
    WorkflowStep,
)


# ── 사전 정의 워크플로우 ──────────────────────────────────────

WEEKLY_PLANNING = Workflow(
    name="주간 기획",
    description="분석팀 리포트 → 기획자 캘린더 수립 (월요일)",
    steps=[
        # 1단계: 분석팀 병렬 실행
        WorkflowStep(
            agent_id="trend-hunter",
            user_message="이번 주 SNS 재테크 트렌드를 분석해주세요. 바이럴 콘텐츠 3~5개를 선정하고, 각각의 성공 요인과 우리 브랜드 적용 아이디어를 제시해주세요.",
        ),
        WorkflowStep(
            agent_id="benchmarking-analyst",
            user_message="벤치마킹 대상 계정들의 이번 주 콘텐츠를 분석해주세요. 성공 패턴 Top 3와 스크루지에 적용할 포인트를 정리해주세요.",
        ),
        WorkflowStep(
            agent_id="performance-analyst",
            user_message="지난 주 우리 콘텐츠 성과를 분석해주세요. 베스트/워스트 콘텐츠를 선정하고 개선 제안 3개를 도출해주세요.",
        ),
        # 2단계: 기획자 (분석 결과 참조)
        WorkflowStep(
            agent_id="reels-planner",
            depends_on=["trend-hunter", "benchmarking-analyst", "performance-analyst"],
            user_message="분석팀 리포트를 참고하여 이번 주 릴스 캘린더(주 2~3개)를 수립해주세요.",
        ),
        WorkflowStep(
            agent_id="threads-planner",
            depends_on=["trend-hunter", "benchmarking-analyst", "performance-analyst"],
            user_message="분석팀 리포트를 참고하여 이번 주 스레드 캘린더(매일 3개, 총 21개)를 수립해주세요.",
        ),
    ],
)

DAILY_THREADS = Workflow(
    name="오늘의 스레드",
    description="오늘의 스레드 3개 작성 (아침/점심/저녁)",
    steps=[
        WorkflowStep(
            agent_id="threads-writer",
            user_message=f"오늘({date.today().isoformat()}) 아침 슬롯 스레드를 작성해주세요. 카테고리: 정보형. 재테크 팁이나 지식을 10줄 이내, 반말+친근 톤으로 작성하세요.",
        ),
        WorkflowStep(
            agent_id="threads-writer",
            user_message=f"오늘({date.today().isoformat()}) 점심 슬롯 스레드를 작성해주세요. 카테고리: 공감형. 일상 속 돈 이야기를 10줄 이내, 반말+친근 톤으로 작성하세요.",
        ),
        WorkflowStep(
            agent_id="threads-writer",
            user_message=f"오늘({date.today().isoformat()}) 저녁 슬롯 스레드를 작성해주세요. 카테고리: 인사이트형. 깊이 있는 경제/투자 생각을 10줄 이내, 반말+친근 톤으로 작성하세요.",
        ),
    ],
)

REELS_FULLSET = Workflow(
    name="릴스 풀세트",
    description="릴스 대본 → 캡션 + 편집가이드 (병렬)",
    steps=[
        WorkflowStep(
            agent_id="reels-scriptwriter",
            user_message="이번 릴스 대본을 작성해주세요. 20~30초 분량, 후킹→본문→CTA 구조로 작성하세요.",
        ),
        WorkflowStep(
            agent_id="caption-dm-writer",
            depends_on=["reels-scriptwriter"],
            user_message="위 릴스 대본에 맞는 캡션과 DM 전송 자료를 작성해주세요.",
        ),
        WorkflowStep(
            agent_id="video-editing-guide",
            depends_on=["reels-scriptwriter"],
            user_message="위 릴스 대본에 맞는 편집 가이드 시트를 작성해주세요. 타임코드별 화면, 자막, 효과를 포함해주세요.",
        ),
    ],
)

DAILY_BRIEFING = Workflow(
    name="데일리 브리핑",
    description="오늘의 경제 뉴스 요약 브리핑 (팬딩)",
    steps=[
        WorkflowStep(
            agent_id="daily-briefer",
            user_message=f"오늘({date.today().isoformat()}) 데일리 브리핑을 작성해주세요. 주요 경제 뉴스 3~5개를 투자자 관점에서 요약하고, 오늘의 인사이트를 제시해주세요.",
        ),
    ],
)

WEEKLY_COLUMN = Workflow(
    name="주간 컬럼",
    description="프리미엄 주간 컬럼 작성 (팬딩)",
    steps=[
        WorkflowStep(
            agent_id="weekly-columnist",
            user_message="이번 주 프리미엄 컬럼을 작성해주세요. A4 4~5페이지 분량, 존댓말+전문가 톤으로 심층 분석 컬럼을 작성하세요.",
        ),
    ],
)

ETF_REPORT = Workflow(
    name="ETF 리포트",
    description="주간 ETF 모니터링 리포트 (팬딩)",
    steps=[
        WorkflowStep(
            agent_id="etf-researcher",
            user_message="이번 주 ETF 모니터링 리포트를 작성해주세요. 카테고리별 수익률 표와 주목 ETF Top 3를 포함해주세요.",
        ),
    ],
)


PRESET_WORKFLOWS: dict[str, Workflow] = {
    "weekly-planning": WEEKLY_PLANNING,
    "daily-threads": DAILY_THREADS,
    "reels-fullset": REELS_FULLSET,
    "daily-briefing": DAILY_BRIEFING,
    "weekly-column": WEEKLY_COLUMN,
    "etf-report": ETF_REPORT,
}


# ── 워크플로우 실행 엔진 ──────────────────────────────────────


async def execute_workflow(
    workflow: Workflow,
    on_step_complete: callable | None = None,
) -> list[AgentRunResult]:
    """워크플로우를 실행합니다.

    의존성이 없는 스텝은 병렬 실행, 의존성이 있으면 순차 실행.

    Args:
        workflow: 실행할 워크플로우
        on_step_complete: 각 스텝 완료 시 호출할 콜백
    """
    agents = load_all_agents()
    results: dict[str, AgentRunResult] = {}
    all_results: list[AgentRunResult] = []

    # 의존성 기반으로 실행 그룹 분리
    remaining = list(workflow.steps)

    while remaining:
        # 현재 실행 가능한 스텝 (의존성이 모두 완료된 것)
        ready = []
        not_ready = []
        for step in remaining:
            if all(dep in results for dep in step.depends_on):
                ready.append(step)
            else:
                not_ready.append(step)

        if not ready:
            # 데드락 — 남은 스텝의 의존성을 해결할 수 없음
            for step in not_ready:
                result = AgentRunResult(
                    agent_id=step.agent_id,
                    status=AgentRunStatus.FAILED,
                    error="의존성 해결 불가 (데드락)",
                )
                all_results.append(result)
            break

        # 실행 가능한 스텝 병렬 실행
        tasks = []
        for step in ready:
            agent = agents.get(step.agent_id)
            if not agent:
                result = AgentRunResult(
                    agent_id=step.agent_id,
                    status=AgentRunStatus.FAILED,
                    error=f"에이전트 '{step.agent_id}'를 찾을 수 없습니다",
                )
                all_results.append(result)
                results[step.agent_id] = result
                continue

            # 의존 에이전트 결과를 컨텍스트로 전달
            context_parts = []
            for dep_id in step.depends_on:
                dep_result = results.get(dep_id)
                if dep_result and dep_result.status == AgentRunStatus.COMPLETED:
                    dep_agent = agents.get(dep_id)
                    dep_name = dep_agent.name if dep_agent else dep_id
                    context_parts.append(
                        f"### {dep_name} 결과:\n{dep_result.content}"
                    )

            context = "\n\n".join(context_parts)
            tasks.append((step, agent, context))

        # 비동기 병렬 실행
        async_tasks = []
        for step, agent, context in tasks:
            from src.core.agent_runner import run_agent_async

            async_tasks.append(
                run_agent_async(agent, step.user_message, context=context)
            )

        batch_results = await asyncio.gather(*async_tasks, return_exceptions=True)

        for (step, _, _), result in zip(tasks, batch_results):
            if isinstance(result, Exception):
                result = AgentRunResult(
                    agent_id=step.agent_id,
                    status=AgentRunStatus.FAILED,
                    error=str(result),
                )

            results[step.agent_id] = result
            all_results.append(result)

            if on_step_complete:
                on_step_complete(result)

        remaining = not_ready

    return all_results
