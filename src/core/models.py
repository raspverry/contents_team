"""도메인 모델 정의.

팀, 에이전트, 워크플로우, 실행 결과 등 모든 도메인 모델의 단일 소스.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── 팀 메타데이터 (단일 소스) ────────────────────────────────


@dataclass(frozen=True)
class TeamMeta:
    display_name: str
    output_dir: str


class TeamType(str, Enum):
    BRANDING = "team1-branding"
    ANALYSIS = "team2-analysis"
    REELS = "team3-reels"
    THREADS = "team4-threads"
    FANDING = "team5-fanding"

    @property
    def meta(self) -> TeamMeta:
        return TEAM_META[self]

    @property
    def display_name(self) -> str:
        return self.meta.display_name

    @property
    def output_dir(self) -> str:
        return self.meta.output_dir


TEAM_META: dict[TeamType, TeamMeta] = {
    TeamType.BRANDING: TeamMeta("🎯 브랜딩 전략팀", "branding"),
    TeamType.ANALYSIS: TeamMeta("🔍 콘텐츠 분석팀", "analysis"),
    TeamType.REELS: TeamMeta("🎬 인스타 릴스 제작팀", "reels"),
    TeamType.THREADS: TeamMeta("🧵 스레드 콘텐츠팀", "threads"),
    TeamType.FANDING: TeamMeta("🎙 팬딩 멤버십팀", "fanding"),
}


# ── 에이전트 ─────────────────────────────────────────────────


class AgentInfo(BaseModel):
    """에이전트 정보."""

    id: str
    name: str
    team: TeamType
    role: str
    frequency: str
    system_prompt: str
    source_file: str


# ── 실행 결과 ────────────────────────────────────────────────


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentRunResult(BaseModel):
    """에이전트 실행 결과."""

    run_id: str
    agent_id: str
    status: RunStatus = RunStatus.PENDING
    content: str = ""
    error: str = ""
    started_at: datetime = Field(default_factory=datetime.now)
    finished_at: datetime | None = None
    tokens_used: int = 0
    output_file: str = ""


# ── 워크플로우 ───────────────────────────────────────────────


class WorkflowStep(BaseModel):
    """워크플로우 단계."""

    agent_id: str
    depends_on: list[str] = Field(default_factory=list)
    message_template: str = ""


class Workflow(BaseModel):
    """워크플로우 정의."""

    id: str
    name: str
    description: str
    steps: list[WorkflowStep]
