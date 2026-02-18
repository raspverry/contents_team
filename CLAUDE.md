# CLAUDE.md — AI Assistant Guide

## Project Overview

**재테크는 스크루지** — 20명의 AI 에이전트가 콘텐츠를 생산하는 1인 회사 운영 시스템.

- 백엔드: FastAPI
- GUI: Streamlit (MVP, 향후 Next.js로 전환)
- 패키지 매니저: uv
- AI: Anthropic Claude API / OpenAI API (`.env`의 `AI_PROVIDER`로 전환)

## Repository Structure

```
contents_team/
├── agents/                      # 에이전트 프롬프트 (마크다운)
│   ├── team1-branding/          #   브랜딩 전략팀 (2명)
│   ├── team2-analysis/          #   콘텐츠 분석팀 (3명)
│   ├── team3-reels/             #   릴스 제작팀 (4명)
│   ├── team4-threads/           #   스레드 콘텐츠팀 (2명)
│   ├── team5-fanding/           #   팬딩 멤버십팀 (4명)
│   └── team6-cardnews/          #   카드뉴스 제작팀 (5명)
├── src/
│   ├── core/
│   │   ├── config.py            # Settings (pydantic-settings), 경로 상수
│   │   ├── models.py            # 도메인 모델: TeamType, AgentInfo, Workflow 등
│   │   └── clients.py           # AI 클라이언트 추상화 (Anthropic/OpenAI)
│   ├── services/
│   │   ├── agent_service.py     # 에이전트 로딩(캐시) + 실행
│   │   ├── workflow_service.py  # 워크플로우 프리셋(팩토리) + 실행 엔진
│   │   ├── output_service.py    # 산출물 조회 (storage 위임)
│   │   └── storage.py           # StorageBackend ABC → FileStorage
│   ├── api/
│   │   ├── server.py            # uvicorn 진입점
│   │   ├── routes.py            # FastAPI 라우트 (얇은 레이어)
│   │   └── schemas.py           # Pydantic 요청/응답 스키마
│   └── gui/
│       └── app.py               # Streamlit GUI
├── workflows/                   # 워크플로우 가이드 문서
├── outputs/                     # 생성된 산출물 (gitignored)
├── pyproject.toml               # uv 프로젝트 설정
├── .env / .env.example          # 환경 변수
└── main.py                      # 안내 메시지 출력
```

## Development Setup

```bash
# 의존성 설치
uv sync

# 환경 변수
cp .env.example .env
# AI_PROVIDER 선택 (anthropic / openai) + 해당 API 키 설정
```

## Commands

| Action | Command |
|--------|---------|
| 의존성 설치 | `uv sync` |
| API 서버 | `uv run api` |
| GUI | `uv run streamlit run src/gui/app.py` |
| API 문서 | http://127.0.0.1:8000/docs |

테스트/린터는 아직 미설정.

## Architecture: Layered Design

```
API Routes (src/api/routes.py)
    ↓ 얇은 라우트: 입력 검증 → 서비스 호출 → 스키마 반환
Services (src/services/)
    ↓ 비즈니스 로직: 에이전트 로딩, 워크플로우 실행, 산출물 관리
Core (src/core/)
    ↓ 도메인 모델, 설정, API 클라이언트
Storage (src/services/storage.py)
    ↓ ABC 기반 추상화: FileStorage → 향후 DB/S3
```

### Key Patterns

- **팀 메타데이터 단일 소스**: `models.py`의 `TeamType` enum + `TEAM_META` dict
- **에이전트 캐시**: `agent_service._agent_cache` — 첫 로드 후 재사용, `force_reload`로 갱신
- **워크플로우 팩토리**: `workflow_service.PRESET_FACTORIES` — `date.today()`가 실행 시점에 평가되도록 팩토리 함수 사용
- **워크플로우 실행**: DAG 기반 의존성 해결, `asyncio.gather`로 병렬 실행, step index 추적 (동일 에이전트 복수 실행 안전)
- **멀티 AI 프로바이더**: `clients.create_message()` 통일 인터페이스 → `AI_PROVIDER` 설정에 따라 Anthropic/OpenAI 자동 전환
- **다국어 콘텐츠**: `CONTENT_LANGUAGE` 설정(`ko`/`ja`/`en`)에 따라 언어별 스타일 가이드가 시스템 프롬프트에 자동 주입. `models.py`의 `LANGUAGE_PROFILES` 단일 소스
- **스토리지 추상화**: `StorageBackend` ABC → `FileStorage` (SaaS 전환 시 교체)
- **파일명**: `YYYY-MM-DD-{agent_id}-{HHMMSSffffff}[-suffix].md` (마이크로초 포함, 중복 방지)
- **경로 보안**: `FileStorage.load()`에서 path traversal 방지

### API Endpoints

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/status` | 시스템 상태 |
| GET | `/api/agents` | 에이전트 목록 |
| GET | `/api/agents/{id}` | 에이전트 상세 |
| POST | `/api/agents/{id}/run` | 에이전트 실행 |
| GET | `/api/workflows` | 워크플로우 목록 |
| POST | `/api/workflows/{id}/run` | 워크플로우 실행 |
| GET | `/api/outputs` | 산출물 목록 |
| GET | `/api/outputs/{team}/{filename}` | 산출물 내용 |

## Agent Prompt Format

`agents/` 디렉토리의 마크다운 파일을 런타임에 파싱:

- **H1**: 에이전트 이름 (한글명 추출)
- **테이블**: `**역할**`, `**실행 빈도**` 행에서 메타데이터 추출
- **`## 시스템 프롬프트`** 섹션의 코드블록: 시스템 프롬프트로 사용
- 파일 stem → agent ID (예: `trend-hunter.md` → `trend-hunter`)

## Code Conventions

- 레이어 분리 준수: routes는 서비스만 호출, 서비스는 core/storage만 사용
- 응답은 항상 `src/api/schemas.py`의 Pydantic 모델 사용
- 새 에이전트 추가: `agents/{team}/` 에 마크다운 파일 추가하면 자동 로딩
- 새 워크플로우 추가: `workflow_service.py`에 팩토리 함수 + `PRESET_FACTORIES`에 등록
- `from __future__ import annotations` 모든 모듈에 포함

## Git Workflow

- **Default branch**: `main`
- Feature branches: `feature/`, `fix/` 접두사
- 커밋 메시지: 변경 이유 중심, 간결하게
- `.env`, 시크릿 커밋 금지

## Tone & Manner Rules

`CONTENT_LANGUAGE` 설정에 따라 자동 전환. 언어별 전체 가이드는 `models.py`의 `LANGUAGE_PROFILES` 참조.

### 한국어 (ko) — 기본

| 채널 | 톤 | 예시 |
|------|-----|------|
| **스레드** | 반말 + 친근 | "적금 이자로는 부자 못 돼. 근데 습관은 만들 수 있어." |
| **릴스** | 친근 + 임팩트 | "월급 300인데 1년에 1000만원 모았습니다" |
| **팬딩 컬럼** | 존댓말 + 전문가 | "이번 주 CPI 데이터의 핵심을 짚어드리겠습니다." |
| **팬딩 브리핑** | 존댓말 + 친근 | "오늘 시장, 한 줄로 정리해드릴게요." |
| **카드뉴스** | 반말 + 정보전달 | "사회초년생 월급관리 5단계" |

### 日本語 (ja)

| チャンネル | トーン | 例 |
|-----------|--------|-----|
| **スレッド/X** | タメ口 + 共感 | "貯金だけじゃお金持ちになれない。でも習慣は作れる。" |
| **リール** | カジュアル + インパクト | "手取り20万で1年で100万貯めた方法" |
| **有料コラム** | 丁寧語 + 専門的 | "今週のCPIデータのポイントを解説いたします。" |
| **ブリーフィング** | 丁寧語 + 親しみ | "今日のマーケット、一言でまとめますね。" |
| **カードニュース** | 簡潔 + わかりやすい | "新社会人の給料管理5ステップ" |

### English (en)

| Channel | Tone | Example |
|---------|------|---------|
| **Threads/X** | Casual + relatable | "Savings accounts won't make you rich. But they build the habit." |
| **Reels/Shorts** | Punchy + hook-driven | "I saved $10K on a $30K salary. Here's how." |
| **Premium column** | Professional + authoritative | "Let's break down this week's CPI data." |
| **Daily briefing** | Conversational + expert | "Here's your one-line market recap for today." |
| **Cardnews** | Clear + actionable | "5 Money Moves for Your First Job" |

## AI Assistant Guidelines

1. **Read before editing** — 파일 수정 전 반드시 읽기
2. **Minimal changes** — 요청된 변경만 수행
3. **No over-engineering** — 추측성 기능 추가 금지
4. **Layer separation** — 라우트에서 직접 로직 작성 금지, 서비스 레이어 사용
5. **Security** — path traversal, 인젝션 등 OWASP Top 10 주의
6. **Update docs** — 구조 변경 시 이 파일 업데이트
7. **톤앤매너 구분** — 채널별 톤을 절대 혼동하지 말 것
8. **투자 면책** — 팬딩 콘텐츠에는 반드시 면책 문구 포함
9. **팩트 체크** — 수치/데이터 인용 시 출처 명시
