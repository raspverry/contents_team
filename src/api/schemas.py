"""API 요청/응답 스키마.

모든 API 엔드포인트의 입출력 형식을 통일합니다.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


# ── 요청 ─────────────────────────────────────────────────────


class RunAgentRequest(BaseModel):
    user_message: str
    context: str = ""


# ── 응답: 에이전트 ───────────────────────────────────────────


class AgentSummary(BaseModel):
    id: str
    name: str
    team: str
    team_display: str
    role: str
    frequency: str


class AgentDetail(AgentSummary):
    system_prompt: str
    source_file: str


class AgentRunResponse(BaseModel):
    run_id: str
    agent_id: str
    status: str
    content: str
    error: str
    tokens_used: int
    output_file: str


# ── 응답: 워크플로우 ────────────────────────────────────────


class WorkflowStepSummary(BaseModel):
    agent_id: str
    depends_on: list[str]


class WorkflowSummary(BaseModel):
    id: str
    name: str
    description: str
    steps: list[WorkflowStepSummary]


class WorkflowRunResponse(BaseModel):
    workflow_id: str
    results: list[AgentRunResponse]


# ── 응답: 산출물 ────────────────────────────────────────────


class OutputSummary(BaseModel):
    team: str
    filename: str
    path: str
    size: int


class OutputContent(BaseModel):
    content: str


# ── 응답: 상태 ──────────────────────────────────────────────


class StatusResponse(BaseModel):
    brand: str
    agents_count: int
    workflows_count: int
    outputs_count: int
    today: str
    ai_provider: str = ""
    ai_model: str = ""
    remotion_available: bool = False


# ── 요청/응답: 렌더링 ────────────────────────────────────────


class RenderCardNewsRequest(BaseModel):
    content_json: dict


class RenderReelsRequest(BaseModel):
    scenes: list[dict]
    brand_name: str = ""


class RenderResultResponse(BaseModel):
    success: bool
    output_path: str = ""
    error: str = ""
    duration_ms: int = 0


class RenderBatchResponse(BaseModel):
    results: list[RenderResultResponse]


# ── 응답: 에러 (통일) ────────────────────────────────────────


class ErrorResponse(BaseModel):
    """모든 에러 응답의 통일 스키마."""

    error: str
    code: str
    detail: str = ""


# ── 응답: 워크플로우 실행 이력 ────────────────────────────────


class WorkflowExecutionSummary(BaseModel):
    execution_id: str
    workflow_id: str
    workflow_name: str
    status: str
    started_at: str
    completed_at: str = ""
    step_count: int = 0
    completed_steps: int = 0
    total_tokens: int = 0


# ── 응답: 테마 프리셋 ──────────────────────────────────────


class ThemePresetResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    colors: dict[str, str]


# ── 요청: 채팅 ─────────────────────────────────────────────


class CreateChatRoomRequest(BaseModel):
    agent_ids: list[str]
    topic: str


class SendChatMessageRequest(BaseModel):
    content: str


# ── 응답: 채팅 ─────────────────────────────────────────────


class ChatMessageResponse(BaseModel):
    id: str
    role: str
    agent_id: str = ""
    agent_name: str = ""
    team: str = ""
    team_display: str = ""
    content: str
    tokens_used: int = 0
    created_at: str


class ChatRoomResponse(BaseModel):
    room_id: str
    topic: str
    agent_ids: list[str]
    messages: list[ChatMessageResponse]
    total_tokens: int = 0
    round_count: int = 0
    created_at: str


class ChatRoundResponse(BaseModel):
    room_id: str
    round_number: int
    messages: list[ChatMessageResponse]
    total_tokens: int = 0
