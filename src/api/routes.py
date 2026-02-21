"""FastAPI 라우트.

얇은 라우트 레이어. 입력 검증 → 서비스 호출 → 스키마 반환.
"""

from __future__ import annotations

import time
from collections import defaultdict
from datetime import date

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from src.api.schemas import (
    AgentDetail,
    AgentRunResponse,
    AgentSummary,
    ChatMessageResponse,
    ChatRoomResponse,
    ChatRoundResponse,
    CreateChatRoomRequest,
    ErrorResponse,
    OutputContent,
    OutputSummary,
    RenderBatchResponse,
    RenderCardNewsRequest,
    RenderReelsRequest,
    RenderResultResponse,
    RunAgentRequest,
    SendChatMessageRequest,
    StatusResponse,
    ThemePresetResponse,
    WorkflowExecutionSummary,
    WorkflowRunResponse,
    WorkflowStepSummary,
    WorkflowSummary,
)
from src.core.config import APP_VERSION, settings
from src.core.models import TeamType
from src.services import agent_service, chat_service, output_service, rendering_service, workflow_service

app = FastAPI(
    title=f"{settings.brand_name} — AI 콘텐츠 팀",
    description="20명의 AI 에이전트가 콘텐츠를 생산하는 1인 회사 운영 시스템",
    version=APP_VERSION,
)


# ── 에러 핸들러 ──────────────────────────────────────────────


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTPException을 통일된 ErrorResponse로 변환."""
    code_map = {400: "BAD_REQUEST", 404: "NOT_FOUND", 429: "RATE_LIMITED", 500: "INTERNAL_ERROR"}
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=str(exc.detail),
            code=code_map.get(exc.status_code, f"HTTP_{exc.status_code}"),
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """예상치 못한 예외를 통일된 ErrorResponse로 변환."""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="서버 내부 오류가 발생했습니다",
            code="INTERNAL_ERROR",
            detail=type(exc).__name__,
        ).model_dump(),
    )


# ── 레이트 리미팅 (인메모리 슬라이딩 윈도우) ────────────────


_rate_buckets: dict[str, list[float]] = defaultdict(list)
_RATE_WINDOW = 60  # 초
_RATE_LIMIT_RUN = settings.rate_limit_run


def _check_rate(key: str, limit: int = _RATE_LIMIT_RUN) -> None:
    """분당 요청 횟수 제한. 초과 시 429."""
    now = time.time()
    bucket = _rate_buckets[key]
    # 윈도우 밖 항목 제거
    _rate_buckets[key] = [t for t in bucket if now - t < _RATE_WINDOW]
    if len(_rate_buckets[key]) >= limit:
        raise HTTPException(429, "요청이 너무 많습니다. 잠시 후 다시 시도해주세요.")
    _rate_buckets[key].append(now)


# ── 에이전트 ─────────────────────────────────────────────────


@app.get("/api/agents", response_model=list[AgentSummary])
def list_agents():
    agents = agent_service.load_all_agents()
    return [
        AgentSummary(
            id=a.id,
            name=a.name,
            team=a.team.value,
            team_display=a.team.display_name,
            role=a.role,
            frequency=a.frequency,
        )
        for a in agents.values()
    ]


@app.get("/api/agents/{agent_id}", response_model=AgentDetail)
def get_agent(agent_id: str):
    agent = agent_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(404, f"에이전트 '{agent_id}'를 찾을 수 없습니다")
    return AgentDetail(
        id=agent.id,
        name=agent.name,
        team=agent.team.value,
        team_display=agent.team.display_name,
        role=agent.role,
        frequency=agent.frequency,
        system_prompt=agent.system_prompt,
        source_file=agent.source_file,
    )


@app.post("/api/agents/{agent_id}/run", response_model=AgentRunResponse)
async def run_single_agent(agent_id: str, req: RunAgentRequest):
    _check_rate("agent_run")

    agent = agent_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(404, f"에이전트 '{agent_id}'를 찾을 수 없습니다")

    result = await agent_service.run_agent(
        agent, req.user_message, context=req.context
    )
    return AgentRunResponse(
        run_id=result.run_id,
        agent_id=result.agent_id,
        status=result.status.value,
        content=result.content,
        error=result.error,
        tokens_used=result.tokens_used,
        output_file=result.output_file,
    )


# ── 워크플로우 ───────────────────────────────────────────────


@app.get("/api/workflows", response_model=list[WorkflowSummary])
def list_workflows():
    workflows = workflow_service.list_preset_workflows()
    return [
        WorkflowSummary(
            id=wf.id,
            name=wf.name,
            description=wf.description,
            steps=[
                WorkflowStepSummary(
                    agent_id=s.agent_id,
                    depends_on=s.depends_on,
                )
                for s in wf.steps
            ],
        )
        for wf in workflows
    ]


@app.post("/api/workflows/{workflow_id}/run", response_model=WorkflowRunResponse)
async def run_workflow(workflow_id: str):
    _check_rate("workflow_run", limit=settings.rate_limit_workflow)

    workflow = workflow_service.get_preset_workflow(workflow_id)
    if not workflow:
        raise HTTPException(404, f"워크플로우 '{workflow_id}'를 찾을 수 없습니다")

    results = await workflow_service.execute_workflow(workflow)
    return WorkflowRunResponse(
        workflow_id=workflow_id,
        results=[
            AgentRunResponse(
                run_id=r.run_id,
                agent_id=r.agent_id,
                status=r.status.value,
                content=r.content,
                error=r.error,
                tokens_used=r.tokens_used,
                output_file=r.output_file,
            )
            for r in results
        ],
    )


@app.get("/api/workflows/history", response_model=list[WorkflowExecutionSummary])
def list_workflow_history(limit: int = 20):
    """워크플로우 실행 이력 조회."""
    return [
        WorkflowExecutionSummary(
            execution_id=ex.execution_id,
            workflow_id=ex.workflow_id,
            workflow_name=ex.workflow_name,
            status=ex.status,
            started_at=ex.started_at.isoformat(),
            completed_at=ex.completed_at.isoformat() if ex.completed_at else "",
            step_count=ex.step_count,
            completed_steps=ex.completed_steps,
            total_tokens=ex.total_tokens,
        )
        for ex in workflow_service.get_execution_history(limit=limit)
    ]


# ── 산출물 ───────────────────────────────────────────────────


@app.get("/api/outputs", response_model=list[OutputSummary])
def list_outputs(team: str | None = None, date_str: str | None = None):
    items = output_service.list_outputs(team=team, date_str=date_str)
    return [
        OutputSummary(
            team=item.team,
            filename=item.filename,
            path=item.path,
            size=item.size,
        )
        for item in items
    ]


@app.get("/api/outputs/{team}/{filename}", response_model=OutputContent)
def get_output(team: str, filename: str):
    content = output_service.get_output_content(team, filename)
    if content is None:
        raise HTTPException(404, "파일을 찾을 수 없습니다")
    return OutputContent(content=content)


# ── 상태 ─────────────────────────────────────────────────────


@app.get("/api/status", response_model=StatusResponse)
def get_status():
    agents = agent_service.load_all_agents()
    outputs = output_service.list_outputs()
    workflows = workflow_service.list_preset_workflows()
    ai_model = (
        settings.openai_model
        if settings.ai_provider == "openai"
        else settings.model
    )
    return StatusResponse(
        brand=settings.brand_name,
        agents_count=len(agents),
        workflows_count=len(workflows),
        outputs_count=len(outputs),
        today=date.today().isoformat(),
        ai_provider=settings.ai_provider,
        ai_model=ai_model,
        remotion_available=rendering_service.is_remotion_available(),
    )


# ── 렌더링 ────────────────────────────────────────────────────


@app.post("/api/render/cardnews/stills", response_model=RenderBatchResponse)
async def render_cardnews_stills(req: RenderCardNewsRequest):
    _check_rate("render")
    results = await rendering_service.render_cardnews_stills(req.content_json)
    return RenderBatchResponse(
        results=[
            RenderResultResponse(
                success=r.success,
                output_path=r.output_path,
                error=r.error,
                duration_ms=r.duration_ms,
            )
            for r in results
        ]
    )


@app.post("/api/render/cardnews/video", response_model=RenderResultResponse)
async def render_cardnews_video(req: RenderCardNewsRequest):
    _check_rate("render")
    r = await rendering_service.render_cardnews_video(req.content_json)
    return RenderResultResponse(
        success=r.success,
        output_path=r.output_path,
        error=r.error,
        duration_ms=r.duration_ms,
    )


@app.post("/api/render/reels", response_model=RenderResultResponse)
async def render_reels(req: RenderReelsRequest):
    _check_rate("render")
    r = await rendering_service.render_reels(
        scenes=req.scenes,
        brand_name=req.brand_name,
    )
    return RenderResultResponse(
        success=r.success,
        output_path=r.output_path,
        error=r.error,
        duration_ms=r.duration_ms,
    )


# ── 테마 프리셋 ──────────────────────────────────────────────


@app.get("/api/themes", response_model=list[ThemePresetResponse])
def list_themes():
    """사용 가능한 카드뉴스 테마 프리셋 목록."""
    result = []
    for theme_id, theme in rendering_service.THEME_PRESETS.items():
        result.append(ThemePresetResponse(
            id=theme_id,
            name=theme_id.replace("-", " ").title(),
            description="",
            category="",
            colors=theme,
        ))
    return result


# ── 팀 채팅 ──────────────────────────────────────────────────


def _chat_msg_to_response(msg: chat_service.ChatMessage) -> ChatMessageResponse:
    """ChatMessage → API 응답 스키마 변환."""
    team_display = ""
    if msg.team:
        try:
            team_display = TeamType(msg.team).display_name
        except ValueError:
            team_display = msg.team
    return ChatMessageResponse(
        id=msg.id,
        role=msg.role.value,
        agent_id=msg.agent_id,
        agent_name=msg.agent_name,
        team=msg.team,
        team_display=team_display,
        content=msg.content,
        tokens_used=msg.tokens_used,
        created_at=msg.created_at.isoformat(),
    )


@app.post("/api/chat/rooms", response_model=ChatRoomResponse)
def create_chat_room(req: CreateChatRoomRequest):
    """채팅 방 생성."""
    try:
        room = chat_service.create_room(req.agent_ids, req.topic)
    except ValueError as e:
        raise HTTPException(400, str(e))

    return ChatRoomResponse(
        room_id=room.room_id,
        topic=room.topic,
        agent_ids=room.agent_ids,
        messages=[_chat_msg_to_response(m) for m in room.messages],
        total_tokens=room.total_tokens,
        round_count=room.round_count,
        created_at=room.created_at.isoformat(),
    )


@app.get("/api/chat/rooms/{room_id}", response_model=ChatRoomResponse)
def get_chat_room(room_id: str):
    """채팅 방 조회 (전체 이력 포함)."""
    room = chat_service.get_room(room_id)
    if not room:
        raise HTTPException(404, f"채팅 방 '{room_id}'를 찾을 수 없습니다")

    return ChatRoomResponse(
        room_id=room.room_id,
        topic=room.topic,
        agent_ids=room.agent_ids,
        messages=[_chat_msg_to_response(m) for m in room.messages],
        total_tokens=room.total_tokens,
        round_count=room.round_count,
        created_at=room.created_at.isoformat(),
    )


@app.post("/api/chat/rooms/{room_id}/messages", response_model=ChatMessageResponse)
def send_chat_message(room_id: str, req: SendChatMessageRequest):
    """사용자 메시지 전송."""
    try:
        msg = chat_service.add_user_message(room_id, req.content)
    except KeyError as e:
        raise HTTPException(404, str(e))

    return _chat_msg_to_response(msg)


@app.post("/api/chat/rooms/{room_id}/round", response_model=ChatRoundResponse)
async def run_chat_round(room_id: str):
    """에이전트 라운드 1회 실행. 모든 에이전트가 순서대로 1번씩 발언."""
    _check_rate("chat_round")

    room = chat_service.get_room(room_id)
    if not room:
        raise HTTPException(404, f"채팅 방 '{room_id}'를 찾을 수 없습니다")

    try:
        round_messages = await chat_service.run_chat_round(room_id)
    except KeyError as e:
        raise HTTPException(404, str(e))

    return ChatRoundResponse(
        room_id=room_id,
        round_number=room.round_count,
        messages=[_chat_msg_to_response(m) for m in round_messages],
        total_tokens=sum(m.tokens_used for m in round_messages),
    )
