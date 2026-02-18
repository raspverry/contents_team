"""FastAPI 라우트.

얇은 라우트 레이어. 입력 검증 → 서비스 호출 → 스키마 반환.
"""

from __future__ import annotations

from datetime import date

from fastapi import FastAPI, HTTPException

from src.api.schemas import (
    AgentDetail,
    AgentRunResponse,
    AgentSummary,
    OutputContent,
    OutputSummary,
    RenderBatchResponse,
    RenderCardNewsRequest,
    RenderReelsRequest,
    RenderResultResponse,
    RunAgentRequest,
    StatusResponse,
    WorkflowRunResponse,
    WorkflowStepSummary,
    WorkflowSummary,
)
from src.core.config import settings
from src.services import agent_service, output_service, rendering_service, workflow_service

app = FastAPI(
    title="재테크는 스크루지 — AI 콘텐츠 팀",
    description="20명의 AI 에이전트가 콘텐츠를 생산하는 1인 회사 운영 시스템",
    version="0.3.0",
)


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
    return StatusResponse(
        brand=settings.brand_name,
        agents_count=len(agents),
        workflows_count=len(workflows),
        outputs_count=len(outputs),
        today=date.today().isoformat(),
        remotion_available=rendering_service.is_remotion_available(),
    )


# ── 렌더링 ────────────────────────────────────────────────────


@app.post("/api/render/cardnews/stills", response_model=RenderBatchResponse)
async def render_cardnews_stills(req: RenderCardNewsRequest):
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
    r = await rendering_service.render_cardnews_video(req.content_json)
    return RenderResultResponse(
        success=r.success,
        output_path=r.output_path,
        error=r.error,
        duration_ms=r.duration_ms,
    )


@app.post("/api/render/reels", response_model=RenderResultResponse)
async def render_reels(req: RenderReelsRequest):
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
