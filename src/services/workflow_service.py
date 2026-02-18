"""워크플로우 서비스.

워크플로우 정의(프리셋)와 실행 엔진을 담당합니다.
워크플로우 정의는 팩토리 함수로, date.today()가 실행 시점에 평가됩니다.
"""

from __future__ import annotations

import asyncio
import uuid
from collections import deque
from datetime import date, datetime
from typing import Callable

from src.core.models import (
    AgentRunResult,
    RunStatus,
    Workflow,
    WorkflowExecution,
    WorkflowStep,
)
from src.services.agent_service import load_all_agents, run_agent


# ── 실행 이력 ────────────────────────────────────────────────

_execution_history: deque[WorkflowExecution] = deque(maxlen=100)


def get_execution_history(*, limit: int = 20) -> list[WorkflowExecution]:
    """최근 워크플로우 실행 이력을 반환 (최신 순)."""
    items = list(_execution_history)
    items.reverse()
    return items[:limit]


# ── 워크플로우 프리셋 (팩토리 함수) ─────────────────────────


def _today() -> str:
    return date.today().isoformat()


def preset_weekly_planning() -> Workflow:
    return Workflow(
        id="weekly-planning",
        name="주간 기획",
        description="분석팀 리포트 → 기획자 캘린더 수립 (월요일)",
        steps=[
            WorkflowStep(
                agent_id="trend-hunter",
                message_template="이번 주 SNS 재테크 트렌드를 분석해주세요. 바이럴 콘텐츠 3~5개를 선정하고, 각각의 성공 요인과 우리 브랜드 적용 아이디어를 제시해주세요.",
            ),
            WorkflowStep(
                agent_id="benchmarking-analyst",
                message_template="벤치마킹 대상 계정들의 이번 주 콘텐츠를 분석해주세요. 성공 패턴 Top 3와 스크루지에 적용할 포인트를 정리해주세요.",
            ),
            WorkflowStep(
                agent_id="performance-analyst",
                message_template="지난 주 우리 콘텐츠 성과를 분석해주세요. 베스트/워스트 콘텐츠를 선정하고 개선 제안 3개를 도출해주세요.",
            ),
            WorkflowStep(
                agent_id="reels-planner",
                depends_on=["trend-hunter", "benchmarking-analyst", "performance-analyst"],
                message_template="분석팀 리포트를 참고하여 이번 주 릴스 캘린더(주 2~3개)를 수립해주세요.",
            ),
            WorkflowStep(
                agent_id="threads-planner",
                depends_on=["trend-hunter", "benchmarking-analyst", "performance-analyst"],
                message_template="분석팀 리포트를 참고하여 이번 주 스레드 캘린더(매일 3개, 총 21개)를 수립해주세요.",
            ),
        ],
    )


def preset_daily_threads() -> Workflow:
    today = _today()
    return Workflow(
        id="daily-threads",
        name="오늘의 스레드",
        description="오늘의 스레드 3개 작성 (아침/점심/저녁)",
        steps=[
            WorkflowStep(
                agent_id="threads-writer",
                message_template=f"오늘({today}) 아침 슬롯 스레드를 작성해주세요. 카테고리: 정보형. 재테크 팁이나 지식을 10줄 이내, 반말+친근 톤으로 작성하세요.",
            ),
            WorkflowStep(
                agent_id="threads-writer",
                message_template=f"오늘({today}) 점심 슬롯 스레드를 작성해주세요. 카테고리: 공감형. 일상 속 돈 이야기를 10줄 이내, 반말+친근 톤으로 작성하세요.",
            ),
            WorkflowStep(
                agent_id="threads-writer",
                message_template=f"오늘({today}) 저녁 슬롯 스레드를 작성해주세요. 카테고리: 인사이트형. 깊이 있는 경제/투자 생각을 10줄 이내, 반말+친근 톤으로 작성하세요.",
            ),
        ],
    )


def preset_reels_fullset() -> Workflow:
    return Workflow(
        id="reels-fullset",
        name="릴스 풀세트",
        description="릴스 대본 → 캡션 + 편집가이드 (병렬)",
        steps=[
            WorkflowStep(
                agent_id="reels-scriptwriter",
                message_template="이번 릴스 대본을 작성해주세요. 20~30초 분량, 후킹→본문→CTA 구조로 작성하세요.",
            ),
            WorkflowStep(
                agent_id="caption-dm-writer",
                depends_on=["reels-scriptwriter"],
                message_template="위 릴스 대본에 맞는 캡션과 DM 전송 자료를 작성해주세요.",
            ),
            WorkflowStep(
                agent_id="video-editing-guide",
                depends_on=["reels-scriptwriter"],
                message_template="위 릴스 대본에 맞는 편집 가이드 시트를 작성해주세요. 타임코드별 화면, 자막, 효과를 포함해주세요.",
            ),
        ],
    )


def preset_daily_briefing() -> Workflow:
    today = _today()
    return Workflow(
        id="daily-briefing",
        name="데일리 브리핑",
        description="오늘의 경제 뉴스 요약 브리핑 (팬딩)",
        steps=[
            WorkflowStep(
                agent_id="daily-briefer",
                message_template=f"오늘({today}) 데일리 브리핑을 작성해주세요. 주요 경제 뉴스 3~5개를 투자자 관점에서 요약하고, 오늘의 인사이트를 제시해주세요.",
            ),
        ],
    )


def preset_weekly_column() -> Workflow:
    return Workflow(
        id="weekly-column",
        name="주간 컬럼",
        description="프리미엄 주간 컬럼 작성 (팬딩)",
        steps=[
            WorkflowStep(
                agent_id="weekly-columnist",
                message_template="이번 주 프리미엄 컬럼을 작성해주세요. A4 4~5페이지 분량, 존댓말+전문가 톤으로 심층 분석 컬럼을 작성하세요.",
            ),
        ],
    )


def preset_etf_report() -> Workflow:
    return Workflow(
        id="etf-report",
        name="ETF 리포트",
        description="주간 ETF 모니터링 리포트 (팬딩)",
        steps=[
            WorkflowStep(
                agent_id="etf-researcher",
                message_template="이번 주 ETF 모니터링 리포트를 작성해주세요. 카테고리별 수익률 표와 주목 ETF Top 3를 포함해주세요.",
            ),
        ],
    )


def preset_cardnews_pipeline() -> Workflow:
    return Workflow(
        id="cardnews-pipeline",
        name="카드뉴스 파이프라인",
        description="리서치 → 레이아웃 설계 → 렌더링 지시서 (3단계 순차)",
        steps=[
            WorkflowStep(
                agent_id="cardnews-researcher",
                message_template="이번 카드뉴스 주제를 리서치하고 기획안을 작성해주세요. 재테크 정보형 주제로, 5~8장 구성, 장별 핵심 내용과 비주얼 제안을 포함해주세요.",
            ),
            WorkflowStep(
                agent_id="layout-designer",
                depends_on=["cardnews-researcher"],
                message_template="위 기획안을 바탕으로 카드별 레이아웃을 설계해주세요. 적절한 블록을 선택하고 content.json 형식으로 구조화해주세요.",
            ),
            WorkflowStep(
                agent_id="cardnews-maker",
                depends_on=["layout-designer"],
                message_template="위 content.json을 바탕으로 카드별 렌더링 지시서를 작성해주세요. 색상, 폰트, 여백, 정렬 등 시각적 디테일을 확정해주세요.",
            ),
        ],
    )


# 프리셋 레지스트리: id → 팩토리 함수
PRESET_FACTORIES: dict[str, Callable[[], Workflow]] = {
    "weekly-planning": preset_weekly_planning,
    "daily-threads": preset_daily_threads,
    "reels-fullset": preset_reels_fullset,
    "daily-briefing": preset_daily_briefing,
    "weekly-column": preset_weekly_column,
    "etf-report": preset_etf_report,
    "cardnews-pipeline": preset_cardnews_pipeline,
}


def get_preset_workflow(workflow_id: str) -> Workflow | None:
    """프리셋 워크플로우를 생성하여 반환 (매번 새로 생성, date 갱신)."""
    factory = PRESET_FACTORIES.get(workflow_id)
    return factory() if factory else None


def list_preset_workflows() -> list[Workflow]:
    """모든 프리셋 워크플로우 목록."""
    return [factory() for factory in PRESET_FACTORIES.values()]


# ── 워크플로우 실행 엔진 ─────────────────────────────────────


async def execute_workflow(
    workflow: Workflow,
    on_step_complete: Callable[[AgentRunResult], None] | None = None,
) -> list[AgentRunResult]:
    """워크플로우를 실행합니다.

    의존성이 없는 스텝은 병렬 실행, 의존성이 있으면 순차 실행.
    같은 에이전트가 여러 번 등장해도 안전하게 처리 (step index 기반 추적).
    실행 이력이 자동으로 기록됩니다.
    """
    # 실행 이력 기록 시작
    execution = WorkflowExecution(
        execution_id=uuid.uuid4().hex[:12],
        workflow_id=workflow.id,
        workflow_name=workflow.name,
        status="running",
        step_count=len(workflow.steps),
    )
    _execution_history.append(execution)

    agents = load_all_agents()
    # step index 기반 추적 (같은 agent_id가 여러 번 올 수 있으므로)
    step_results: dict[int, AgentRunResult] = {}
    all_results: list[AgentRunResult] = []

    # depends_on은 agent_id 기반 → step index로 변환
    # 같은 agent_id의 가장 최근 step을 참조
    agent_last_step: dict[str, int] = {}
    step_deps: dict[int, list[int]] = {}

    for i, step in enumerate(workflow.steps):
        deps_indices = []
        for dep_agent_id in step.depends_on:
            if dep_agent_id in agent_last_step:
                deps_indices.append(agent_last_step[dep_agent_id])
        step_deps[i] = deps_indices
        agent_last_step[step.agent_id] = i

    remaining = set(range(len(workflow.steps)))
    completed = set()

    while remaining:
        # 실행 가능한 스텝 (의존성 모두 완료)
        ready = [
            i for i in remaining
            if all(dep in completed for dep in step_deps[i])
        ]

        if not ready:
            for i in remaining:
                step = workflow.steps[i]
                result = AgentRunResult(
                    run_id=f"deadlock-{i}",
                    agent_id=step.agent_id,
                    status=RunStatus.FAILED,
                    error="의존성 해결 불가 (데드락)",
                )
                all_results.append(result)
            break

        # 병렬 실행
        async_tasks = []
        ready_indices = []

        for i in ready:
            step = workflow.steps[i]
            agent = agents.get(step.agent_id)

            if not agent:
                result = AgentRunResult(
                    run_id=f"not-found-{i}",
                    agent_id=step.agent_id,
                    status=RunStatus.FAILED,
                    error=f"에이전트 '{step.agent_id}'를 찾을 수 없습니다",
                )
                step_results[i] = result
                all_results.append(result)
                completed.add(i)
                remaining.discard(i)
                if on_step_complete:
                    on_step_complete(result)
                continue

            # 의존 스텝 결과를 컨텍스트로 조합
            context_parts = []
            for dep_i in step_deps[i]:
                dep_result = step_results.get(dep_i)
                if dep_result and dep_result.status == RunStatus.COMPLETED:
                    dep_agent = agents.get(dep_result.agent_id)
                    dep_name = dep_agent.name if dep_agent else dep_result.agent_id
                    context_parts.append(
                        f"### {dep_name} 결과:\n{dep_result.content}"
                    )
            context = "\n\n".join(context_parts)

            async_tasks.append(
                run_agent(agent, step.message_template, context=context)
            )
            ready_indices.append(i)

        if async_tasks:
            batch_results = await asyncio.gather(
                *async_tasks, return_exceptions=True
            )

            for idx, batch_result in zip(ready_indices, batch_results):
                if isinstance(batch_result, Exception):
                    batch_result = AgentRunResult(
                        run_id=f"error-{idx}",
                        agent_id=workflow.steps[idx].agent_id,
                        status=RunStatus.FAILED,
                        error=str(batch_result),
                    )

                step_results[idx] = batch_result
                all_results.append(batch_result)
                completed.add(idx)
                remaining.discard(idx)

                if on_step_complete:
                    on_step_complete(batch_result)

    # 실행 이력 기록 완료
    has_failure = any(r.status == RunStatus.FAILED for r in all_results)
    execution.status = "completed" if not has_failure else "partial_failure"
    execution.completed_at = datetime.now()
    execution.completed_steps = sum(
        1 for r in all_results if r.status == RunStatus.COMPLETED
    )
    execution.total_tokens = sum(r.tokens_used for r in all_results)

    return all_results
