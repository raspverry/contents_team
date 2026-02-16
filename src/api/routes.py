"""FastAPI 라우트 정의."""

from __future__ import annotations

import asyncio
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.core.agent_loader import load_all_agents
from src.core.agent_runner import run_agent_async
from src.core.config import OUTPUTS_DIR
from src.core.models import AgentRunResult, AgentRunStatus, TEAM_DISPLAY
from src.core.workflow_engine import PRESET_WORKFLOWS, execute_workflow

app = FastAPI(
    title="재테크는 스크루지 — AI 콘텐츠 팀",
    description="15명의 AI 에이전트가 콘텐츠를 생산하는 1인 회사 운영 시스템",
    version="0.1.0",
)


# ── 요청/응답 모델 ─────────────────────────────────────────


class RunAgentRequest(BaseModel):
    user_message: str
    context: str = ""


class RunWorkflowRequest(BaseModel):
    custom_messages: dict[str, str] = {}  # agent_id → 커스텀 메시지


# ── 에이전트 API ────────────────────────────────────────────


@app.get("/api/agents")
def list_agents():
    """전체 에이전트 목록 반환."""
    agents = load_all_agents()
    return [
        {
            "id": a.id,
            "name": a.name,
            "team": a.team.value,
            "team_display": TEAM_DISPLAY[a.team],
            "role": a.role,
            "frequency": a.frequency,
        }
        for a in agents.values()
    ]


@app.get("/api/agents/{agent_id}")
def get_agent(agent_id: str):
    """특정 에이전트 상세 정보."""
    agents = load_all_agents()
    agent = agents.get(agent_id)
    if not agent:
        raise HTTPException(404, f"에이전트 '{agent_id}'를 찾을 수 없습니다")
    return {
        "id": agent.id,
        "name": agent.name,
        "team": agent.team.value,
        "team_display": TEAM_DISPLAY[agent.team],
        "role": agent.role,
        "frequency": agent.frequency,
        "system_prompt": agent.system_prompt,
        "source_file": agent.source_file,
    }


@app.post("/api/agents/{agent_id}/run")
async def run_single_agent(agent_id: str, req: RunAgentRequest):
    """단일 에이전트 실행."""
    agents = load_all_agents()
    agent = agents.get(agent_id)
    if not agent:
        raise HTTPException(404, f"에이전트 '{agent_id}'를 찾을 수 없습니다")

    result = await run_agent_async(agent, req.user_message, context=req.context)
    return {
        "agent_id": result.agent_id,
        "status": result.status.value,
        "content": result.content,
        "error": result.error,
        "tokens_used": result.tokens_used,
        "output_file": result.output_file,
    }


# ── 워크플로우 API ──────────────────────────────────────────


@app.get("/api/workflows")
def list_workflows():
    """사전 정의 워크플로우 목록."""
    return [
        {
            "id": wf_id,
            "name": wf.name,
            "description": wf.description,
            "steps": [
                {
                    "agent_id": s.agent_id,
                    "depends_on": s.depends_on,
                }
                for s in wf.steps
            ],
        }
        for wf_id, wf in PRESET_WORKFLOWS.items()
    ]


@app.post("/api/workflows/{workflow_id}/run")
async def run_workflow(workflow_id: str, req: RunWorkflowRequest | None = None):
    """워크플로우 실행."""
    workflow = PRESET_WORKFLOWS.get(workflow_id)
    if not workflow:
        raise HTTPException(404, f"워크플로우 '{workflow_id}'를 찾을 수 없습니다")

    results = await execute_workflow(workflow)
    return {
        "workflow": workflow_id,
        "results": [
            {
                "agent_id": r.agent_id,
                "status": r.status.value,
                "content": r.content[:500] + "..." if len(r.content) > 500 else r.content,
                "error": r.error,
                "tokens_used": r.tokens_used,
                "output_file": r.output_file,
            }
            for r in results
        ],
    }


# ── 산출물 API ──────────────────────────────────────────────


@app.get("/api/outputs")
def list_outputs(team: str | None = None, date_str: str | None = None):
    """산출물 목록 조회."""
    items = []
    for subdir in OUTPUTS_DIR.iterdir():
        if not subdir.is_dir():
            continue
        if team and subdir.name != team:
            continue
        for f in sorted(subdir.glob("*.md"), reverse=True):
            if date_str and not f.name.startswith(date_str):
                continue
            items.append(
                {
                    "team": subdir.name,
                    "filename": f.name,
                    "path": str(f),
                    "size": f.stat().st_size,
                }
            )
    return items


@app.get("/api/outputs/{team}/{filename}")
def get_output(team: str, filename: str):
    """산출물 내용 조회."""
    filepath = OUTPUTS_DIR / team / filename
    if not filepath.exists():
        raise HTTPException(404, "파일을 찾을 수 없습니다")
    return {"content": filepath.read_text(encoding="utf-8")}


# ── 상태 API ────────────────────────────────────────────────


@app.get("/api/status")
def get_status():
    """시스템 상태."""
    agents = load_all_agents()
    output_count = sum(
        1
        for subdir in OUTPUTS_DIR.iterdir()
        if subdir.is_dir()
        for _ in subdir.glob("*.md")
    )
    return {
        "brand": "재테크는 스크루지",
        "agents_count": len(agents),
        "workflows_count": len(PRESET_WORKFLOWS),
        "outputs_count": output_count,
        "today": date.today().isoformat(),
    }
