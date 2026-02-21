"""도메인 모델 정의.

팀, 에이전트, 워크플로우, 실행 결과 등 모든 도메인 모델의 단일 소스.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# ── 언어별 스타일 가이드 (단일 소스) ─────────────────────────


@dataclass(frozen=True)
class LanguageProfile:
    """콘텐츠 언어 프로필."""

    code: str
    label: str
    instruction: str
    style_guide: str


LANGUAGE_PROFILES: dict[str, LanguageProfile] = {
    "ko": LanguageProfile(
        code="ko",
        label="한국어",
        instruction="모든 콘텐츠를 한국어로 작성하세요.",
        style_guide=(
            "## 한국어 콘텐츠 스타일 가이드\n"
            "- 스레드: 반말 + 친근 (예: '적금 이자로는 부자 못 돼. 근데 습관은 만들 수 있어.')\n"
            "- 릴스: 친근 + 임팩트 (예: '월급 300인데 1년에 1000만원 모았습니다')\n"
            "- 팬딩 컬럼: 존댓말 + 전문가 (예: '이번 주 CPI 데이터의 핵심을 짚어드리겠습니다.')\n"
            "- 팬딩 브리핑: 존댓말 + 친근 (예: '오늘 시장, 한 줄로 정리해드릴게요.')\n"
            "- 카드뉴스: 반말 + 정보전달 (예: '사회초년생 월급관리 5단계')\n"
            "- 플랫폼: Instagram, Threads, 네이버 블로그\n"
            "- MZ세대 트렌드 용어를 자연스럽게 활용\n"
            "- 숫자/금액은 한국 원화(₩) 기준"
        ),
    ),
    "ja": LanguageProfile(
        code="ja",
        label="日本語",
        instruction="すべてのコンテンツを日本語で作成してください。",
        style_guide=(
            "## 日本語コンテンツスタイルガイド\n"
            "- スレッド/X: タメ口 + 共感型 (例: '貯金だけじゃお金持ちになれない。でも習慣は作れる。')\n"
            "- リール: カジュアル + インパクト (例: '手取り20万で1年で100万貯めた方法')\n"
            "- 有料コラム: 丁寧語 + 専門的 (例: '今週のCPIデータのポイントを解説いたします。')\n"
            "- デイリーブリーフィング: 丁寧語 + 親しみ (例: '今日のマーケット、一言でまとめますね。')\n"
            "- カードニュース: 簡潔 + わかりやすい (例: '新社会人の給料管理5ステップ')\n"
            "- プラットフォーム: X (Twitter), Instagram, note, YouTube Shorts\n"
            "- Z世代・ミレニアル世代に響く表現を使用\n"
            "- 金額は日本円(¥)基準"
        ),
    ),
    "en": LanguageProfile(
        code="en",
        label="English",
        instruction="Write all content in English.",
        style_guide=(
            "## English Content Style Guide\n"
            "- Threads/X: Casual + relatable (e.g., 'Savings accounts won't make you rich. But they build the habit.')\n"
            "- Reels/Shorts: Punchy + hook-driven (e.g., 'I saved $10K on a $30K salary. Here's how.')\n"
            "- Premium columns: Professional + authoritative (e.g., 'Let's break down this week's CPI data.')\n"
            "- Daily briefing: Conversational + expert (e.g., 'Here's your one-line market recap for today.')\n"
            "- Cardnews: Clear + actionable (e.g., '5 Money Moves for Your First Job')\n"
            "- Platforms: Instagram, TikTok, X, Substack/Newsletter\n"
            "- Use Gen Z / millennial-friendly language naturally\n"
            "- Amounts in USD ($) by default"
        ),
    ),
}


def get_language_profile(code: str) -> LanguageProfile:
    """언어 코드로 프로필 조회. 미지원 언어는 ko 폴백."""
    return LANGUAGE_PROFILES.get(code, LANGUAGE_PROFILES["ko"])


def inject_language_guide(system_prompt: str, content_language: str = "ko") -> str:
    """비한국어 환경에서 시스템 프롬프트에 언어 가이드를 주입."""
    lang = get_language_profile(content_language)
    if lang.code == "ko":
        return system_prompt
    return system_prompt + f"\n\n## 콘텐츠 언어\n{lang.instruction}\n\n{lang.style_guide}"


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
    CARDNEWS = "team6-cardnews"

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
    TeamType.CARDNEWS: TeamMeta("🎨 카드뉴스 제작팀", "cardnews"),
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


# ── 워크플로우 실행 이력 ──────────────────────────────────────


class WorkflowExecution(BaseModel):
    """워크플로우 실행 이력 레코드."""

    execution_id: str
    workflow_id: str
    workflow_name: str
    status: str = "running"
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None
    step_count: int = 0
    completed_steps: int = 0
    total_tokens: int = 0


# ── 품질 검증 ────────────────────────────────────────────────


class ReviewVerdict(str, Enum):
    """품질 검증 최종 판정."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class QualityCheck(BaseModel):
    """개별 검증 항목 결과."""

    check_id: str
    category: str
    name: str
    verdict: ReviewVerdict
    score: int = 0
    detail: str = ""
    suggestion: str = ""


class QualityReport(BaseModel):
    """2-Phase 품질 검증 통합 보고서."""

    report_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    content_preview: str = ""
    agent_id: str = ""

    brand_checks: list[QualityCheck] = Field(default_factory=list)
    brand_score: int = 0
    brand_verdict: ReviewVerdict = ReviewVerdict.PASS

    content_checks: list[QualityCheck] = Field(default_factory=list)
    content_score: int = 0
    content_verdict: ReviewVerdict = ReviewVerdict.PASS

    overall_score: int = 0
    overall_verdict: ReviewVerdict = ReviewVerdict.PASS
    tokens_used: int = 0
    reviewed_at: datetime = Field(default_factory=datetime.now)


# ── 채팅 ─────────────────────────────────────────────────────


class ChatRole(str, Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """채팅 메시지 한 건."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    role: ChatRole
    agent_id: str = ""
    agent_name: str = ""
    team: str = ""
    content: str
    tokens_used: int = 0
    created_at: datetime = Field(default_factory=datetime.now)


class ChatRoom(BaseModel):
    """채팅 방."""

    room_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    topic: str
    agent_ids: list[str]
    messages: list[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    total_tokens: int = 0
    round_count: int = 0
