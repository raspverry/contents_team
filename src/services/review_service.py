"""품질 검증 서비스.

콘텐츠의 브랜드 가이드라인 준수(Phase 1)와 콘텐츠 품질(Phase 2)을
AI 에이전트로 자동 검증합니다.
"""

from __future__ import annotations

import json
import re
from collections import deque
from datetime import datetime

from src.core.config import BASE_DIR
from src.core.models import (
    QualityCheck,
    QualityReport,
    ReviewVerdict,
    RunStatus,
)
from src.services.agent_service import _substitute_brand_vars, get_agent, run_agent


# ── 상수 ─────────────────────────────────────────────────────

BRAND_GUIDELINES_PATH = BASE_DIR / "brand-guidelines.md"
_BRAND_REVIEWER_ID = "brand-reviewer"
_CONTENT_REVIEWER_ID = "content-reviewer"
_CONTENT_PREVIEW_LEN = 200

_review_history: deque[QualityReport] = deque(maxlen=200)


# ── 디폴트 브랜드 가이드라인 ─────────────────────────────────

_DEFAULT_GUIDELINES = """\
# {{brand_name}} 브랜드 가이드라인

## 톤 & 보이스

### 채널별 톤 규칙
| 채널 | 톤 | 예시 |
|------|-----|------|
| **스레드** | 반말 + 친근 | "적금 이자로는 부자 못 돼. 근데 습관은 만들 수 있어." |
| **릴스** | 친근 + 임팩트 | "월급 300인데 1년에 1000만원 모았습니다" |
| **팬딩 컬럼** | 존댓말 + 전문가 | "이번 주 CPI 데이터의 핵심을 짚어드리겠습니다." |
| **팬딩 브리핑** | 존댓말 + 친근 | "오늘 시장, 한 줄로 정리해드릴게요." |
| **카드뉴스** | 반말 + 정보전달 | "사회초년생 월급관리 5단계" |

### 금지 표현
- 비속어, 혐오 표현
- 다른 브랜드/인물 비하
- "무조건", "반드시", "100%" 등 단정적 표현 (투자 관련)

## 포맷 규칙
| 채널 | 길이 | 구조 |
|------|------|------|
| **스레드** | 5~10줄 | 후킹 → 본문 → CTA |
| **릴스 대본** | 20~30초 분량 | 후킹(5초) → 본문(15~20초) → CTA(5초) |
| **카드뉴스** | 5~8장 | 커버 → 본문 카드 → CTA |
| **팬딩 컬럼** | A4 4~5페이지 | 서론 → 분석 → 결론 → 면책 |

## 면책 조항
팬딩 콘텐츠에는 반드시 포함: "{{brand_disclaimer}}"

## 금지 콘텐츠
- 특정 종목 매수/매도 추천
- 확정적 수익률 보장 표현
- 검증되지 않은 수치의 출처 없는 인용

## 해시태그 규칙
- 필수: {{brand_handle}}
- 개수: 5~10개

## CTA 규칙
- 모든 콘텐츠에 1개 이상의 CTA 포함
"""


# ── 가이드라인 관리 ─────────────────────────────────────────


def load_brand_guidelines() -> str:
    """brand-guidelines.md를 로드하고 {{brand_*}} 변수를 치환."""
    if not BRAND_GUIDELINES_PATH.exists():
        return ""
    raw = BRAND_GUIDELINES_PATH.read_text(encoding="utf-8")
    return _substitute_brand_vars(raw)


def load_brand_guidelines_raw() -> str:
    """brand-guidelines.md 원본 텍스트 (치환 전). GUI 편집용."""
    if not BRAND_GUIDELINES_PATH.exists():
        return _DEFAULT_GUIDELINES
    return BRAND_GUIDELINES_PATH.read_text(encoding="utf-8")


def save_brand_guidelines(content: str) -> None:
    """brand-guidelines.md 저장."""
    BRAND_GUIDELINES_PATH.write_text(content, encoding="utf-8")


def get_default_brand_guidelines() -> str:
    """디폴트 브랜드 가이드라인 텍스트 반환."""
    return _DEFAULT_GUIDELINES


# ── 핵심 공개 API ────────────────────────────────────────────


async def review_content(
    content: str,
    *,
    agent_id: str = "",
    channel_hint: str = "",
) -> QualityReport:
    """콘텐츠에 대해 2-phase 품질 검증을 실행.

    Args:
        content: 검증할 콘텐츠 텍스트
        agent_id: 콘텐츠를 생성한 에이전트 ID
        channel_hint: 채널 힌트 ("threads", "reels" 등)
    """
    report = QualityReport(
        content_preview=content[:_CONTENT_PREVIEW_LEN],
        agent_id=agent_id,
    )

    guidelines = load_brand_guidelines()
    total_tokens = 0

    # Phase 1: 브랜드 가이드라인 준수
    brand_checks, brand_tokens = await _run_phase(
        reviewer_id=_BRAND_REVIEWER_ID,
        content=content,
        category="brand",
        extra_context=f"## 브랜드 가이드라인\n{guidelines}" if guidelines else "",
        channel_hint=channel_hint,
    )
    report.brand_checks = brand_checks
    report.brand_score = _compute_average_score(brand_checks)
    report.brand_verdict = _compute_verdict(brand_checks)
    total_tokens += brand_tokens

    # Phase 2: 콘텐츠 품질
    content_checks, content_tokens = await _run_phase(
        reviewer_id=_CONTENT_REVIEWER_ID,
        content=content,
        category="content",
        extra_context="",
        channel_hint=channel_hint,
    )
    report.content_checks = content_checks
    report.content_score = _compute_average_score(content_checks)
    report.content_verdict = _compute_verdict(content_checks)
    total_tokens += content_tokens

    # 종합
    report.overall_score = (report.brand_score + report.content_score) // 2
    report.overall_verdict = _worst_verdict(
        report.brand_verdict, report.content_verdict
    )
    report.tokens_used = total_tokens
    report.reviewed_at = datetime.now()

    _review_history.append(report)
    return report


def get_review_history(*, limit: int = 20) -> list[QualityReport]:
    """최근 검증 이력 (최신 순)."""
    items = list(_review_history)
    items.reverse()
    return items[:limit]


# ── 내부 헬퍼 ────────────────────────────────────────────────


async def _run_phase(
    *,
    reviewer_id: str,
    content: str,
    category: str,
    extra_context: str,
    channel_hint: str,
) -> tuple[list[QualityCheck], int]:
    """한 Phase를 실행하고 QualityCheck 리스트를 반환."""
    reviewer = get_agent(reviewer_id)
    if not reviewer:
        return [
            QualityCheck(
                check_id="reviewer-not-found",
                category=category,
                name="리뷰어 에이전트 없음",
                verdict=ReviewVerdict.WARN,
                score=0,
                detail=f"에이전트 '{reviewer_id}'를 찾을 수 없습니다",
            )
        ], 0

    context_parts = []
    if extra_context:
        context_parts.append(extra_context)
    if channel_hint:
        context_parts.append(f"## 채널 정보\n이 콘텐츠의 채널: {channel_hint}")

    user_message = (
        f"다음 콘텐츠를 검증해주세요:\n\n---\n{content}\n---\n\n"
        f"위 콘텐츠에 대해 모든 검증 항목을 평가하고 JSON으로 응답하세요."
    )

    result = await run_agent(
        reviewer,
        user_message,
        context="\n\n".join(context_parts),
        save_output=False,
    )

    if result.status != RunStatus.COMPLETED:
        return [
            QualityCheck(
                check_id="review-failed",
                category=category,
                name="검증 실패",
                verdict=ReviewVerdict.WARN,
                score=0,
                detail=f"검증 실행 실패: {result.error}",
            )
        ], result.tokens_used

    checks = _parse_review_response(result.content, category)
    return checks, result.tokens_used


def _parse_review_response(
    raw_response: str, category: str
) -> list[QualityCheck]:
    """AI 응답(JSON)을 QualityCheck 리스트로 파싱."""
    text = raw_response.strip()

    # 코드 펜스 래핑 제거
    if "```" in text:
        match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
        if match:
            text = match.group(1).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return [
            QualityCheck(
                check_id="parse-error",
                category=category,
                name="응답 파싱 실패",
                verdict=ReviewVerdict.WARN,
                score=50,
                detail=f"AI 응답을 JSON으로 파싱할 수 없습니다: {raw_response[:200]}",
            )
        ]

    checks: list[QualityCheck] = []
    for item in data.get("checks", []):
        verdict_str = item.get("verdict", "warn").lower()
        try:
            verdict = ReviewVerdict(verdict_str)
        except ValueError:
            verdict = ReviewVerdict.WARN

        checks.append(
            QualityCheck(
                check_id=item.get("check_id", "unknown"),
                category=category,
                name=item.get("name", ""),
                verdict=verdict,
                score=max(0, min(100, int(item.get("score", 50)))),
                detail=item.get("detail", ""),
                suggestion=item.get("suggestion", ""),
            )
        )

    return checks if checks else [
        QualityCheck(
            check_id="empty-response",
            category=category,
            name="검증 결과 없음",
            verdict=ReviewVerdict.WARN,
            score=50,
            detail="AI가 검증 항목을 반환하지 않았습니다",
        )
    ]


def _compute_average_score(checks: list[QualityCheck]) -> int:
    """검증 항목들의 평균 점수."""
    if not checks:
        return 0
    return sum(c.score for c in checks) // len(checks)


def _compute_verdict(checks: list[QualityCheck]) -> ReviewVerdict:
    """검증 항목들의 최종 판정 (가장 나쁜 결과 기준)."""
    if not checks:
        return ReviewVerdict.PASS
    if any(c.verdict == ReviewVerdict.FAIL for c in checks):
        return ReviewVerdict.FAIL
    if any(c.verdict == ReviewVerdict.WARN for c in checks):
        return ReviewVerdict.WARN
    return ReviewVerdict.PASS


def _worst_verdict(a: ReviewVerdict, b: ReviewVerdict) -> ReviewVerdict:
    """두 판정 중 더 나쁜 것을 반환."""
    order = {ReviewVerdict.PASS: 0, ReviewVerdict.WARN: 1, ReviewVerdict.FAIL: 2}
    return a if order[a] >= order[b] else b
