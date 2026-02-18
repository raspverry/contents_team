"""API 요청/응답 스키마.

모든 API 엔드포인트의 입출력 형식을 통일합니다.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


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
    remotion_available: bool = False


# ── 요청/응답: 렌더링 ────────────────────────────────────────


class RenderCardNewsRequest(BaseModel):
    content_json: dict


class RenderReelsRequest(BaseModel):
    scenes: list[dict]
    brand_name: str = "재테크는 스크루지"


class RenderResultResponse(BaseModel):
    success: bool
    output_path: str = ""
    error: str = ""
    duration_ms: int = 0


class RenderBatchResponse(BaseModel):
    results: list[RenderResultResponse]
