"""데이터 모델 정의."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TeamType(str, Enum):
    BRANDING = "team1-branding"
    ANALYSIS = "team2-analysis"
    REELS = "team3-reels"
    THREADS = "team4-threads"
    FANDING = "team5-fanding"


TEAM_DISPLAY = {
    TeamType.BRANDING: "🎯 브랜딩 전략팀",
    TeamType.ANALYSIS: "🔍 콘텐츠 분석팀",
    TeamType.REELS: "🎬 인스타 릴스 제작팀",
    TeamType.THREADS: "🧵 스레드 콘텐츠팀",
    TeamType.FANDING: "🎙 팬딩 멤버십팀",
}


class AgentInfo(BaseModel):
    """에이전트 정보."""

    id: str  # 파일명 기반 (예: "trend-hunter")
    name: str  # 한글 이름 (예: "트렌드 헌터")
    team: TeamType
    role: str  # 역할 설명
    frequency: str  # 실행 빈도
    system_prompt: str  # 시스템 프롬프트
    source_file: str  # 원본 md 파일 경로


class AgentRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentRunResult(BaseModel):
    """에이전트 실행 결과."""

    agent_id: str
    status: AgentRunStatus
    content: str = ""
    error: str = ""
    started_at: datetime = Field(default_factory=datetime.now)
    finished_at: datetime | None = None
    tokens_used: int = 0
    output_file: str = ""


class WorkflowStep(BaseModel):
    """워크플로우 단계."""

    agent_id: str
    depends_on: list[str] = Field(default_factory=list)
    user_message: str = ""
    context: dict[str, Any] = Field(default_factory=dict)


class Workflow(BaseModel):
    """워크플로우 정의."""

    name: str
    description: str
    steps: list[WorkflowStep]
